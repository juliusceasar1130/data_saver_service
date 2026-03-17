# Git Subtree 模块化开发指南

本文档总结了如何将主项目中的子目录（如 `savedatabase`）提取为独立仓库，并通过 Git Subtree 保持同步的完整流程。

---

## 🏗️ 第一阶段：提取与初始化 (从现有目录开始)

### 1. 提取历史记录
在主项目根目录下执行：
```bash
git subtree split --prefix=savedatabase -b savedatabase-branch
```
*   **原因**：主项目的提交记录包含了全项目的文件。此命令会扫描 `savedatabase` 目录的所有变动，并将其“克隆”到一个全新的本地分支 `savedatabase-branch` 中，此时该分支只包含该目录的代码和历史。

### 2. 创建独立仓库
```bash
# 创建新文件夹
mkdir f:\000_dev\Python\workplace\savedatabase_repo
cd f:\000_dev\Python\workplace\savedatabase_repo

# 初始化仓库并同步内容
git init
git checkout -b main
git pull f:\000_dev\Python\workplace\skid_count_websoket savedatabase-branch
```
*   **原因**：建立一个完全独立的物理文件夹作为“镜像”，方便在以后进行单独的版本控制或分享给其他项目。

---

## 🔗 第二阶段：建立主从关联

### 1. 在主项目中添加远程引用
在主项目根目录下执行：
```bash
git remote add savedatabase f:\000_dev\Python\workplace\savedatabase_repo
```
*   **原因**：告诉主项目，“以后如果你想找 `savedatabase` 模块的独立仓库，就去这个路径找”。

### 2. 配置独立仓库以允许直接推送 (核心优化)
在 **独立仓库** 目录中执行：
```bash
git config receive.denyCurrentBranch updateInstead
```
*   **原因**：默认情况下，Git 禁止向已打开的工作区推送。开启此选项后，当你从主项目执行 `push` 时，独立仓库会**自动更新磁盘上的文件**，无需手动执行 pull，实现了“一处修改，双向同步”。

---

## 🚀 第三阶段：日常开发流

### 情况 A：在主项目中修改并推送到独立仓库
1.  **提交代码**（必须先 commit）：
    ```bash
    git add savedatabase/xxx.py
    git commit -m "update database logic"
    ```
2.  **推送同步**：
    ```bash
    git subtree push --prefix=savedatabase savedatabase main
    ```
*   **注意**：同步的是“提交记录”，如果文件没有 commit，`subtree push` 会提示 `up-to-date` 从而忽略你的改动。

### 情况 B：在独立仓库中修改并拉取到主项目
1.  在独立仓库提交并推送后，在主项目执行：
    ```bash
    git subtree pull --prefix=savedatabase savedatabase main --squash
    ```
*   **--squash 的好处**：它会将独立仓库中的一连串小提交合并为一个大提交再合并进主项目，防止主项目的历史记录变得过于凌乱。

---

## 💡 常见问题排查
*   **提示 "Everything up-to-date" 但文件没动？**
    请检查你是否忘记在当前项目中 `git commit`。Subtree 只搬运已提交的记录。
*   **提示 "refusing to update checked out branch"？**
    请确保在独立仓库中执行了 `updateInstead` 配置（见第二阶段第2步）。
