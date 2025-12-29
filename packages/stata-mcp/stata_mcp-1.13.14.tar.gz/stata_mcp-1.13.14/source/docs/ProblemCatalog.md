# Problem Catalog
- [🇨🇳 中文](#已知问题)
- [🇬🇧 English](#known-problems)

---

# 已知问题
针对该项目，目前已发现以下问题，欢迎通过 issue 或 PR 进行补充：

## 懒惰
在缺乏合适提示词的情况下（即便偶尔给出较好的提示词也会如此），模型在使用 Stata-MCP 时常表现出“懒惰”行为：
- 执行任务时不主动读取 log 文件；
- 集成读取 log 的操作后，只编写 do-file 而不执行；
- 即使流程全部整合，仍可能只返回文本代码而不真正生成 do-file。

## 蝴蝶效应
在执行 do-file 时若出现小错误，模型往往难以自行解决，从而不断尝试（通常是错误方法），形成死循环。这通常源于其对 Stata 语法的不熟悉。

---

# Known Problems
The following issues have been observed in this project. Feel free to open an issue or submit a PR if you discover more.

## Laziness
Without well-crafted prompts (and sometimes even with them), the model tends to act lazily when using Stata-MCP:
- It skips reading log files during execution;
- After log reading is added to the do-file, it may only write the do-file without running it;
- Even when all steps are combined, the model might output the code as plain text instead of actually writing a do-file.

## Butterfly Effect
When a minor error occurs while running a do-file, the model often fails to resolve it and keeps trying incorrect fixes, leading to an infinite loop. This behavior usually stems from limited familiarity with Stata syntax.
