# 调用 scapegoat CLI

画像建档、附身这些主线功能是纯 markdown，不需要任何命令。只有下面这些要用 CLI：字节预算校验、语料归一化、freeze、rollout、benchmark。

按顺序尝试，第一个可用的就用：

1. **`scapegoat <args>`** —— 用户已经装过（`uv tool install`）时最快。
2. **`uvx --from git+ssh://git@github.com/colehank/scapegoat scapegoat <args>`** —— 未安装时的零安装路径。uv 会自动拉代码建环境，首次略慢，之后有缓存。仓库是私有的，所以用 SSH 形式——HTTPS 在没有凭证时会失败。
3. **都不可用**（没有 uv 也没装包）：不要中断任务。告诉用户这一步被跳过、以及装上后能得到什么，然后继续。字节预算这类校验可以用 `wc -c` 手工核对——默认上限是 `profile.md` 6144 字节、每个 `analyse/*.md` 10240 字节，画像目录下若有 `budget.json` 则以它为准。

判断是否可用：`command -v scapegoat` / `command -v uvx`，不要靠试错报错来判断。
