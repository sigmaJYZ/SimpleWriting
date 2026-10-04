"""Tests for lint_hook_fork.py, the fork's entry point of the two advisory hooks."""
import json, os, pathlib, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent
HOOK = HERE / "lint_hook_fork.py"
CLEAN = {"CLAUDE_CONFIG_DIR": "/nonexistent/claude-config", "SIMPLE_ENGLISH_LINT_EXCLUDE": ""}
ZH_LONG = "词" * 50 + "。"
ZH_OK = "sqlpipe 把 Postgres 表复制到 S3。它需要一个配置文件。如果凭证不正确，S3 会拒绝上传。\n"
IT = ("Per utilizzare il comando, è necessario utilizzare un file di configurazione. Il programma copia le tabelle su S3 "
      "e utilizza le credenziali del profilo. Se le credenziali non sono corrette, il servizio rifiuta il caricamento dei dati. "
      "Gli utenti possono utilizzare una chiave diversa per ogni ambiente, e il navigatore mostra realmente lo stato.\n")
RU = ("Vue — это фреймворк для создания пользовательских интерфейсов. Он создан на стандартах HTML, CSS и JavaScript.\n"
      "Компонент — это часть интерфейса, и её можно использовать много раз в одном приложении без изменений.\n")

def run(event, env=None):
    r = subprocess.run([sys.executable, str(HOOK)], input=json.dumps(event), capture_output=True, text=True,
                       env={**os.environ, **CLEAN, **(env or {})})
    return r.returncode, r.stdout, r.stderr

def write(directory, text, name="notes.md"):
    path = pathlib.Path(directory, name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return str(path)

def post(path, **tool_input):
    return {"hook_event_name": "PostToolUse", "tool_name": "Write", "tool_input": {"file_path": path, **tool_input}}

def stop(reply):
    code, out, err = run({"hook_event_name": "Stop", "last_assistant_message": reply})
    assert code == 0, (code, err)
    return json.loads(out)["systemMessage"] if out.strip() else ""

def test_the_upstream_suite_passes_through_the_fork_entry():
    """English text and every path rule must behave as upstream does."""
    import test_lint_hook as upstream_tests
    upstream_tests.HOOK = HOOK
    ran = [fn() for name, fn in vars(upstream_tests).items() if name.startswith("test_")]
    assert len(ran) >= 16, len(ran)

def test_a_long_chinese_sentence_gets_a_hit_with_its_line():
    with tempfile.TemporaryDirectory() as d:
        code, out, err = run(post(write(d, "# 标题\n\n第一句很短。\n\n" + ZH_LONG + "\n")))
    assert code == 2 and "writing hit(s) (zh)" in err and "line 5, sentence_over_limit" in err, (code, err)

def test_a_chinese_file_gets_its_own_checks():
    text = "值得注意的是，这个步骤至关重要。\n\n我们对系统进行测试；然后重启——再看日志。\n"
    with tempfile.TemporaryDirectory() as d:
        code, out, err = run(post(write(d, text)))
    assert code == 2, (code, err)
    for hit in ("line 1, slop_word: 值得注意的是", "line 1, slop_word: 至关重要", "line 3, semicolon: ；", "line 3, em_dash: —"):
        assert hit in err, (hit, err)
    assert "has 4 writing hit(s)" in err, err

def test_a_clean_chinese_file_passes():
    with tempfile.TemporaryDirectory() as d:
        assert run(post(write(d, ZH_OK)))[0] == 0

def test_an_edit_to_a_chinese_file_is_judged_on_the_lines_it_touched():
    old = (ZH_LONG + "\n\n") * 3
    with tempfile.TemporaryDirectory() as d:
        path = write(d, old + "新的一句很短。\n\n新的长句" + ZH_LONG + "\n\n" + "词" * 30 + "新加的片段" + "词" * 30 + "。\n")
        assert run(post(path))[0] == 2, "a write is judged on the whole file"
        assert run(post(path, old_string="旧", new_string="新的一句很短。"))[0] == 0
        code, out, err = run(post(path, old_string="旧", new_string="新的长句" + ZH_LONG))
        assert code == 2 and "has 1 writing hit(s)" in err and "line 9, sentence_over_limit: 新的长句" in err, (code, err)
        # A few words put inside a long sentence: the fragment is short, and the sentence is not.
        code, out, err = run(post(path, old_string="旧", new_string="新加的片段"))
    assert code == 2 and "has 1 writing hit(s)" in err and "line 11, sentence_over_limit" in err, (code, err)

def test_italian_words_get_no_english_hit():
    with tempfile.TemporaryDirectory() as d:
        code, out, err = run(post(write(d, IT)))
    assert code == 0, (code, err)

def test_a_long_italian_sentence_still_gets_a_hit():
    long = "Il programma copia " + "le tabelle e " * 12 + "le invia al servizio. "
    with tempfile.TemporaryDirectory() as d:
        code, out, err = run(post(write(d, long + IT)))
    assert code == 2 and "sentence_over_limit" in err and "slop_word" not in err, (code, err)

def test_a_russian_dash_gets_no_hit():
    with tempfile.TemporaryDirectory() as d:
        assert run(post(write(d, RU)))[0] == 0

def test_an_excluded_path_stays_excluded_for_chinese():
    with tempfile.TemporaryDirectory() as d:
        assert run(post(write(pathlib.Path(d, ".claude", "memory"), ZH_LONG, "MEMORY.md")))[0] == 0
        path = write(d, ZH_LONG)
        assert run(post(path), env={"SIMPLE_ENGLISH_LINT_EXCLUDE": f"{d}/*.md"})[0] == 0

def test_a_file_that_the_hook_cannot_read_never_blocks():
    assert run(post("/nonexistent/folder/notes.md"))[0] == 0
    with tempfile.TemporaryDirectory() as d:
        assert run(post(write(d, "")))[0] == 0, "an empty file"
        path = pathlib.Path(d, "gbk.md")
        path.write_bytes(("词" * 60 + "。").encode("gbk"))
        assert run(post(str(path)))[0] == 0, "a file that is not UTF-8"
        pathlib.Path(d, "folder.md").mkdir()
        assert run(post(str(pathlib.Path(d, "folder.md"))))[0] == 0, "a folder with a .md name"

def test_an_edit_with_text_that_is_not_in_the_file_is_judged_on_the_whole_file():
    with tempfile.TemporaryDirectory() as d:
        path = write(d, ZH_LONG + "\n")
        code, out, err = run(post(path, old_string="旧", new_string="这段文字不在文件里。"))
    assert code == 2 and "line 1, sentence_over_limit" in err, (code, err)

def test_stop_flags_a_chinese_opener_closer_and_slop_word():
    msg = stop("好的！这个接口是幂等的，这一点至关重要。重试是安全的。希望这对你有帮助！")
    assert "opener" in msg and "closer" in msg and "slop" in msg, msg

def test_stop_counts_a_chinese_dash_once():
    assert "1 em-dash(s)" in stop("重试是安全的——因为这个接口是幂等的。")

def test_stop_permits_the_dash_in_a_russian_reply():
    assert stop("Vue — это фреймворк для интерфейсов. Компонент — это часть интерфейса, и её можно использовать много раз.") == ""
    assert "em-dash" in stop("The deploy failed — the disk was full.")

def test_stop_is_silent_on_a_good_chinese_reply():
    assert stop("重试是安全的，因为这个接口是幂等的（重复执行的结果相同）。你不需要改脚本。") == ""
    assert stop("好的做法是先写数据库，再删缓存。如果有问题，日志会记录原因。") == ""

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("ok", name)
