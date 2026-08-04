# Generator-Discriminator 对抗系统 · 架构设计

> 一个模拟特定 Discriminator 行为、驱动交付物迭代打磨的多 Agent 对抗系统，
> 支持真实意见实时注入、画像持续学习与跨会话持久化。

---

## 系统概述

借鉴生成对抗网络（GAN）的对抗迭代思路：Generator 持续生成与修订交付物，Discriminator 持续发散批评，两者通过对齐层学习真实行为，最终收敛至满足 Discriminator 标准的交付物。

系统分为四层：**IO层、模型层、对齐层、编排层**。

---

## IO层

系统所有数据的唯一入口，只做一件事：**归一化**。

识别输入数据类型（语音、文本、图像、文档），转换为系统内部 schema：

- 外部 Profile 数据 → Profile schema
- Task 数据 → Task schema
- Message 数据 → Message schema
- 训练记录 → TrainingRecord schema：`{task, deliverable, real_discriminator_output}`

归一化完成后，数据交给编排层处理。IO层不做路由决策。

---

## 模型层

包含两个非对称的模型单元，均不直接接触真实数据。

### Discriminator + Discriminator Profile

Discriminator 模拟真实 Discriminator 的行为，生成发散批评意见。

Discriminator Profile 是其行为参数，记录：
- 发散偏好（横向扩展 vs 纵向深挖的权重）
- 批评模式（触发条件 → 发散方向 → 典型句式）
- 收敛条件（何种状态下停止追问）
- 版本化管理，由对齐层负责更新

首次使用前，用户需手动提供初始 Discriminator Profile，描述真实 Discriminator 的已知行为特征作为冷启动种子。此后由对齐层持续更新。

Discriminator 每轮输出除内容外，还附带结构化收敛信号 `{converged: true/false}`，由自身根据 Profile 中的收敛条件判断生成。编排层只读取这个 flag，不解释自然语言。

### Generator + Generator Profile

Generator 生成交付物，内部分两层：
- **防御层**：根据 Profile 主动规避 Discriminator 已知痛点
- **响应层**：针对本轮收到的具体意见做修订

Generator Profile 记录的是**生成策略**，而非 Discriminator 标准的镜像：
- 修订策略：历史上哪类修法在收到批评后有效
- 规避策略：哪类内容倾向于触发 Discriminator 批评
- 执行风格偏好
- 版本化管理，由对齐层负责更新

Generator Profile 空启动，不需要用户提供初始种子——第一轮 Generator 生成朴素交付物，经第一次训练 session 后 Profile 自然积累。

Generator 不记录、不依赖对 Discriminator 评判标准的理解。类比 GAN：Generator 不读 Discriminator 的权重，只接收「这次有效/无效」的梯度信号，将理解隐式编码在自己的策略里。

### 运行时行为

两个模型运行时：
- 各自读取自己的 Profile
- 从编排层获取 Task、当前最优交付物和 Runtime 历史作为上下文
- 生成输出后写回编排层的 Runtime 历史；Generator 输出同时更新当前最优交付物

---

## 对齐层

系统的学习引擎，只在**训练 session** 中运行，由编排层在 TrainingRecord 注入后触发。

### 损失计算

对比 TrainingRecord 中真实 Discriminator 输出与模拟 Discriminator 对同一交付物的输出，识别差异。差异以结构化自然语言描述：
- 模拟多说了什么（过度发散的方向，需要降权）
- 模拟漏掉了什么（真实关注但未捕捉到的维度）
- 语气、句式、逻辑方向哪里偏了

### 画像更新

基于损失描述，分别更新两个 Profile，更新方向不同：

- **Discriminator Profile 更新**：调整评判标准、发散偏好、收敛条件，使模拟行为更接近真实 Discriminator
- **Generator Profile 更新**：只写入「本次修订策略是否有效」，记录哪类修法在真实 Discriminator 那里奏效，不写入 Discriminator 的评判标准

Profile 版本号递增，更新后写回模型层。

### 有效性验证

不做独立验证步骤——每次损失计算本身就是对上一轮更新的验证。流程：

```
计算当前损失
  → 与上一次训练 session 的损失对比
  → 损失缩小：上一版 Profile 有效，继续更新
  → 损失增大：上一版 Profile 有害，回滚至上一版本，再更新
  → 记录本次损失值供下轮对比
```

---

## 编排层

系统的大脑，承担**流程控制**和**会话状态管理**两类职责。

### 路由分发

接收 IO 层归一化后的数据，按类型分发：
- Profile → 模型层
- Task → 编排层（写入 Task 状态）
- Message → 编排层（写入 Runtime 历史）
- TrainingRecord → 训练 session 触发对齐层

### Session 类型管理

编排层管理两种独立的 session 类型：

**推理 session**：驱动 Discriminator-Generator 交替循环，Profile 在整个 session 内只读，不允许对齐层介入。

**训练 session**：接收 TrainingRecord，对齐层运行，更新 Profile。训练 session 结束后，以更新后的 Profile 开启新的推理 session。

两种 session 不在同一上下文中切换。TrainingRecord 注入时，当前推理 session 暂停，训练 session 完成后自动开启新推理 session，用户感知为无缝继续。

### 会话状态管理

编排层维护三类生命周期不同的状态：

**Task**：会话种子，来自 IO 层，写入后不可变，整个 session 内全局可见。包含：
- 任务描述与目标
- 发起方（generator / discriminator / external）
- 隐性或显性的完成标准

**Runtime 历史**：当前 session 的完整对话列表，Discriminator 和 Generator 的输出均追加写入。类比 GAN 的单轮 forward pass，用完即丢——session 结束后清空，训练 session 完成开启新推理 session 时同样清空。

**当前最优交付物**：Generator 在本 Task 内迄今最新的一版输出。在训练/推理 session 切换时**保留**，新推理 session 开启后 Generator 以此为起点继续修订，而非从零生成。Task 收敛后清空。类比 GAN 的 best sample，是跨 session 的任务进度锚点。

### 流程控制

**启动决策**：读取 Runtime 历史最近一条：
- 最近是 Generator 输出 → 启动 Discriminator
- 最近是 Discriminator 输出 → 启动 Generator
- 冷启动（仅有 Task，Runtime 历史为空）→ 启动 Generator

冷启动永远由 Generator 先跑。Discriminator 的职责是批评交付物，没有交付物 Discriminator 无法开口。Task 的发起方字段仅用于归因，不影响流程控制。

**循环控制**：驱动 Discriminator 和 Generator 交替运行，接收 Discriminator 输出的结构化收敛信号，决定是否结束当前推理 session。

**交付物输出**：收到 Discriminator 的 `{converged: true}` 信号后，直接输出当前最优交付物，清空 Runtime 历史与当前最优交付物，Profile 持久化。

---

## 完整数据流

```
外部输入（任意模态）
  → IO层归一化
  → 编排层路由分发
    → Profile 流向模型层
    → Task / Message 写入编排层状态
    → TrainingRecord 触发训练 session

编排层启动决策（推理 session）
  → 冷启动或有历史 → 激活 Discriminator 或 Generator

模型读取：Profile + Task + 当前最优交付物 + Runtime 历史
  → 生成输出（Discriminator 附带收敛 flag）
  → Generator 输出写回 Runtime 历史
  → Generator 输出同步更新当前最优交付物

编排层读取收敛 flag
  → converged: false → 继续循环
  → converged: true  → 直接输出交付物 → 清空 Runtime 历史 + 当前最优交付物 → Profile 持久化

TrainingRecord 注入
  → 推理 session 暂停
  → 开启训练 session，触发对齐层

对齐层计算损失
  → 与上一次损失对比（延迟验证上一轮更新有效性）
  → 更新 Discriminator Profile（评判标准）
  → 更新 Generator Profile（修订策略有效性）
  → 更新后的 Profile 写回模型层

训练 session 结束
  → Runtime 历史清空
  → 当前最优交付物保留
  → 以新 Profile + 当前最优交付物开启新推理 session
```

---

## 四层职责速查

| 层 | 核心职责 | 输入 | 输出 |
|---|---|---|---|
| **IO层** | 多模态归一化 | 语音 / 文本 / 图像 / 文档 | Profile / Task / Message / TrainingRecord schema |
| **模型层** | Discriminator + Generator 对抗生成 | Profile + Task + 当前最优交付物 + Runtime历史 | 批评意见（含收敛 flag）/ 交付物草稿 |
| **对齐层** | 损失计算 + 延迟验证 + 画像更新（仅训练 session）| TrainingRecord + 模拟输出 + 上一版损失值 | 更新后的 Profile |
| **编排层** | 路由分发 + 会话管理 + 循环驱动 + 交付输出 | 归一化数据 + TrainingRecord | 交付物 / 触发信号 |

---

## 设计原则

**数据隔离**：模型层不直接接触真实数据，TrainingRecord 只流向对齐层，经抽象后以 Profile 形式影响模型行为，防止模型"记住答案"。

**单一入口**：所有外部数据必须经过 IO 层归一化，系统内部只处理统一 schema。IO 层只做归一化，不做路由。

**Profile 职责非对称**：Discriminator Profile 记录评判标准，Generator Profile 记录生成策略。Generator 不读 Discriminator 的评判标准，只从修订结果的有效性信号中学习，防止退化为影子副本。

**三态分离**：编排层维护三类生命周期不同的状态——Profile（跨 session 持久）、当前最优交付物（Task 内持久，跨训练/推理 session 保留）、Runtime 历史（session 内短暂，用完即丢）。类比 GAN：权重对应 Profile，best sample 对应当前最优交付物，forward pass 对应 Runtime 历史。

**训练/推理隔离**：推理 session 内 Profile 只读，对齐层只在训练 session 中运行。两种 session 不在同一上下文中切换，避免 Runtime 历史与 Profile 版本错位。

**控制流与语义分离**：编排层只读结构化信号（收敛 flag），不解释自然语言。语义判断由模型层负责。
