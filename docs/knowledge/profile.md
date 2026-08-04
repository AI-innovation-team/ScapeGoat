# **认知人工智能中的人类行为预测：基于心理学与认知科学的Agent画像构建与上下文注入范式**

## **引言**

随着生成式人工智能（Generative AI）架构的不断演进，大型语言模型（LLM）的应用边界正在从传统的自然语言理解与内容生成，向着具备深度认知、反思能力以及长期一致性社会行为特征的自主代理（Autonomous Agents）领域拓展。在社会科学、行为经济学、公共政策测试以及人机交互的临床心理学领域，利用人工智能代理来模拟和预测真实人类个体的行为反应，展现出了极具突破性的理论与应用价值。近期的实证研究，特别是斯坦福大学主导的关于利用生成式代理模拟一千名真实人类的研究表明，通过结合深度定性访谈的逐字稿与大型语言模型，AI代理在复刻真实个体对综合社会调查（General Social Survey, GSS）等问卷的回答时，其准确率高达85%，这一惊人的表现甚至与人类参与者在相隔两周后重复作答自身的内部一致性相媲美 1。  
然而，实现如此高保真度的人类行为预测并非易事。仅仅依赖于传统的人口统计学标签（如年龄、性别、种族、收入水平或政治倾向）来构建代理的身份上下文，往往会触发基础大型语言模型中固有的训练集偏见与算法单作（Algorithmic Monoculture），导致行为预测沦为对某种社会刻板印象的机械复读，而非对具体个体真实认知过程的模拟 5。真实的人类行为具有高度的情境依赖性、时间连续性、情感驱动性以及内在动机的复杂交织。因此，要构造一个能够被有效注入代理上下文窗口（Context Window）的“个体画像”（Human Profile），需要从认知科学、神经生物学以及人格心理学等前沿理论中汲取架构灵感。  
本研究报告旨在全面、系统且深刻地解构这一多维代理画像的构建与注入范式。报告将首先探讨如何将心理学中从静态特质到动态情境交互的人格模型抽象为大语言模型的系统指令与约束条件；随后，深入解析包括语义图谱与情景记忆在内的多重记忆流架构；接着，探讨如何通过模拟人类的双系统认知、认知评估理论与躯体标记假说，赋予代理非理性的情感演算机制；最后，全面剖析将这些复杂认知结构工程化注入代理上下文的具体实现路径与表示工程技术。

## **第一部分：认知与心理学理论基础下的多维Profile构建与参数化**

构建一个能够精准预测人类行为的自主代理，其核心工程在于确立稳固且具有深度的心理学架构。传统的基于词袋或基础特征向量的自然语言处理方法往往将人格视为单一的、扁平维度的集合。然而，现代心理学广泛认同人格是一个多层次、动态交互的复杂认知与情感处理系统。这就要求我们在构建代理画像时，必须实现从宏观结构到微观情境触发器的全景式建模。

### **静态特质、特征性适应与生命叙事的三层人格建构**

在构建代理画像的初始基线时，麦克亚当斯（McAdams）提出的“三层人格模型”（Three-Level Personality Model）为刻画个体提供了一个强有力的、可直接向大模型上下文转译的结构学框架 9。该模型主张人格应当被划分为三个相互嵌套但运作机制各异的递进层次。这三个层次分别对应了代理在上下文管理中从硬性底层约束到柔性生成空间的不同技术配置逻辑。  
第一层是个体的特质层（Dispositional Traits）。这是个体的生物学基础，体现了跨越不同情境的广泛一致性与反应倾向 11。在代理画像的工程构建中，这一层通常采用大五人格（Big Five：开放性、责任心、外向性、宜人性、神经质）或更详尽的HEXACO模型来进行参数化定义。研究证实，大五人格特征以及HEXACO中特有的诚实-谦逊（Honesty-Humility）、情感性（Emotionality）等维度，可以有效映射至大型语言模型的深层激活向量中，从而在底层机制上诱发相关的行为倾向 14。例如，高责任心的代理在多步任务规划中会表现出更强的秩序感与纠错意愿，而高宜人性的代理在社会博弈环境中更容易表现出合作倾向，尽管这也可能增加其被剥削的风险 15。在实际应用中，这一层通常以系统提示（System Prompt）中的显性量表分数或特定激活神经元权重的方式存在，确立代理的基础反应基线。  
第二层是特征性适应层（Characteristic Adaptations）。特质层虽然稳定，但缺乏对特定角色和特定时间下行为变化的解释力。特征性适应涉及个体在特定生活领域中形成的动机、特定目标、应对策略和防御机制等 11。在代理的语境中，这意味着画像必须包含特定领域的偏好权重，比如对于特定政治议题的态度倾向、对某些社会现象的特定防备心理等。当特征性适应机制被编入代理时，大型语言模型就能更精准地评估不同情境线索对特定角色的威胁或机遇程度，这使得行为预测真正超越了刻板印象，展现出更细腻的个体差异。  
第三层，也是最为复杂和核心的一层，是生命叙事层（Life Narratives）。生命叙事是个体用来整合过去、现在与未来的内在故事结构，赋予生活以目的感和连贯的自我同一性 11。在基于真实人类仿真的生成式代理研究中，生命叙事是画像的最核心数据来源。通过将数小时的深度定性访谈逐字稿、自传体记忆或长时间维度的个人数字足迹转化为代理的底层语料库，代理不仅获得了有关该人类对象的事实陈述，更习得了该个体独特的叙事语气、解释世界的深层逻辑以及价值评估体系 1。

| 人格层次理论模型 (McAdams) | 心理学内涵与行为表现 | 代理画像(Profile)中的对应计算实现方式 | 在预测模型中的核心功能与价值 |
| :---- | :---- | :---- | :---- |
| **特质层 (Dispositional Traits)** | 具备跨情境广泛一致性的生物学基础特征，如大五人格、HEXACO模型。 | 全局系统提示词(System Prompt)，显性标注的人格维度分数或通过底层表征工程微调激活的隐性表征向量。 | 决定代理的基础反应基线与通用倾向，如基础社交活跃度、风险承受能力的底座。 |
| **特征性适应 (Characteristic Adaptations)** | 动机、短期/中长期目标、应对机制、角色特定信念与价值观。 | 带有情境触发条件的规则集，或在特定知识域下的偏好权重矩阵；基于KAPA模型的自我图式编码。 | 提供高度情境依赖的差异化反应，合理解释“同一人在不同社交压力或角色设定下的迥异表现”。 |
| **生命叙事 (Life Narratives)** | 个人传记、关键闪回记忆、自我同一性的建构与连贯的生命意义体系。 | 由深度定性访谈逐字稿、日记或历史交互文本转化而来的高维情景记忆库与高阶抽象反思（Reflection）。 | 赋予代理真实的人类主体感与高度个性化的叙事逻辑，主导复杂伦理与开放式困境中的决策。 |

### **动态认知-情感处理系统与情境感知的融合**

仅仅依赖静态的人格量表，不足以解释人类行为跨情境波动的巨大差异。著名心理学家米歇尔（Mischel）与肖田（Shoda）联合提出的“认知-情感人格系统”（Cognitive-Affective Personality System, CAPS）理论深刻指出，个体的行为在不同情境下虽然看似多变，但这种对特定情境产生的特定反应规律（即“情境-行为特征”，Situation-Behavior Signatures）本身却是极其稳定且具有人格代表性的 19。该理论将人格视为一个高度动态的认知-情感处理单元网络。  
在将CAPS框架理论转移到代理模型中时，构建画像意味着必须建立一系列内部的“认知-情感单元”（Cognitive-Affective Units, CAUs）。这一单元网络包含五个核心处理模块：编码（Encodings，个体如何识别和分类特定刺激）、期望与信念（Expectancies and Beliefs，个体对行为后果或事件发展的主观预测）、情感（Affects，伴随特定认知产生的生理与心理情绪反应）、目标与价值观（Goals and Values）以及能力与自我调节计划（Competencies and Self-regulatory Plans，个体为了实现目标而制定的行动策略） 21。  
为了在以大型语言模型驱动的代理中激活这一复杂网络，近期研究提出了一种名为角色身份激活（Role Identity Activation, RIA）的方法，通过精准的提示词工程与检索增强，将人类复杂的情感映射为系统中的情感模块，将人类的历史经验与立场映射为编码与信念，将深层动机映射为目标与价值观 22。当环境发生改变时，RIA机制促使代理在接收到新上下文后，动态激活与该情境高度绑定的CAU子网络，从而防范模型在长周期多轮交互中经常出现的“人设漂移”现象。  
与之密切相关的还有“知识与评估人格架构”（Knowledge and Appraisal Personality Architecture, KAPA）模型 9。KAPA模型强调必须将关于“自我的知识”与对特定情况的“评估”区分开来。在代理架构中，这要求数据库中既要存储脱离情境的“自我图式（Self-schemas）”，也要存储高度情境化的“情境信念（Situational Beliefs）” 25。例如，在一项利用KAPA模型理解高风险情境下吸烟者自我效能感的研究中表明，通过实验性地激活特定效价的自我知识，可以高度情境化地改变个体的应对评估 27。同样，在代理画像注入时，我们不仅要告诉大模型“你是一个意志坚定的人”，还需要通过上下文激活其特定的情境信念，使其像真实人类一样，在某些特定高压场景下表现出与其一贯特质相反的脆弱性。

### **深层动机、需求层次与成人依恋系统的底层驱动**

如果说特质与认知评估决定了代理行为的“模式”，那么动机理论与依恋机制则提供了行为的“燃料”与深层安全基线。在构建复杂代理体系时，注入自我决定理论（Self-Determination Theory, SDT）与马斯洛需求层次理论（Maslow's Hierarchy of Needs）能够显著提升代理行为的长效连贯性与自发涌现能力 28。  
自我决定理论深刻强调了个体对于自主性（Autonomy，成为行为主体的渴望）、胜任感（Competence，有效应对环境的能力感）和归属感（Relatedness，与他人建立安全而深厚联系的需求）的基本心理需求 29。当为代理设计奖励函数或长期目标导向提示时，区分其驱动力是外在规则奖励（如简单的任务完成度打分）还是内在的心理需求满足，将产生截然不同的演化结果。以内在需求驱动的代理，在遇到环境阻碍时往往能展现出更加类似于人类的灵活变通和长久坚持，而不会像传统算法那样陷入局部最优解的死锁 29。  
在更深邃的社交关系仿真层面，依恋理论（Attachment Theory）提供了一个不可或缺的画像维度。由约翰·鲍尔比（John Bowlby）建立的这一理论指出，个体根据早期与主要照顾者的互动经验，会形成稳定的“内部工作模式”（Internal Working Models, IWMs） 33。根据对自身（认为自己是否值得被爱）和对他人（认为他人是否值得信赖）的积极或消极认知，依恋风格被划分为安全型、焦虑型、回避型以及恐惧-回避型等 33。  
在最新一代的医疗与心理评估人工智能中，依恋理论被深度整合入多代理系统（Multi-Agent Systems）。例如，在模拟成人依恋访谈（Adult Attachment Interview, AAI）的环境中，研究人员引入了检索增强生成技术（RAG）来合成带有特定童年创伤记忆的虚拟受访者档案 34。更进一步地，一项基于自我依恋技术（Self-Attachment Technique, SAT）的随机对照试验表明，利用有限状态机（FSM）对齐治疗阶段并结合共享长期记忆的多代理系统，在自然度、共情表达和类人感方面，以压倒性优势超越了无引导的基础大语言模型对话机器人 36。这充分说明，在构建个体画像时，将其关系图谱与依恋焦虑/回避维度的内部工作模式进行参数化耦合，是实现高阶社群互动仿真与情感预测的核心钥匙。

## **第二部分：记忆流架构与高维知识图谱的认知表征**

人类认知并非是一个每次都从零开始无状态调用的纯数学函数，而是基于过往海量经验不断演化、巩固和重构的动态网络系统。要实现对个体行为的长效精准预测，人工智能代理绝对不能仅仅依赖大型语言模型有限的上下文窗口（Context Window）进行局限的单轮或少轮次交互推断，而必须具备一套在架构学上能够深度模拟人类神经系统记忆机制的底层支持系统。

### **多重记忆形态的神经科学抽象与数据库对应**

在最先进的生成式代理体系架构中，记忆管理模块构成了认知模型的跳动心脏 37。为了保证行为预测的逼真度和历史连贯性，代理的记忆系统必须在工程架构上严格区分几种不同功能属性的记忆形态，这与认知心理学中的分类高度吻合 40：  
第一类为工作记忆（Working Memory）。在人类大脑中，工作记忆扮演着短期信息缓冲与处理中枢的角色。映射到代理架构中，这体现为系统在当前处理周期内维持活跃状态的信息变量，包括正在进行的对话轮次历史、当前紧迫任务的目标描述以及基础的系统规则限制。由于大语言模型注意力机制的限制，工作记忆往往受到严格的容量控制。  
第二类为情景记忆（Episodic Memory）。这是个人对特定时间、地点及情境下发生的事件序列的具体记录。在认知代理中，情景记忆以自然语言事件日志的形式广泛存在，详细记录了代理生命周期中的具体经历（例如“昨天早上九点在超市遇到了曾经的竞争对手”）。在底层技术实现上，情景记忆通常借助于支持高维语义向量检索与精确时间戳过滤的向量数据库（如Elasticsearch的混合检索方案）来进行存储与读取 41。这种记忆对于代理维持长期叙事连贯性至关重要。  
第三类为语义记忆（Semantic Memory）。与带有强烈时间与空间锚点的情景记忆不同，语义记忆是脱离了具体发生情境的抽象事实、世界运行规则、概念字典以及稳定的自我核心价值观认知。在企业级AI代理应用中，公司手册、产品规格均属于语义记忆。在人类模拟代理中，语义记忆优先支持高召回率的概念级检索，旨在为复杂的因果推理奠定基础常识背景 41。  
第四类则是过程记忆（Procedural Memory）。它主要关乎“如何做”，即执行特定复杂任务的工作流规范。在语言代理体系中，隐性的过程记忆常常固化于大模型的神经网络权重深处，而显性的过程记忆则作为编写在代理代码库中的决策树、工具调用图谱或是操作程序逻辑存在。改变过程记忆往往伴随着较高的风险，因为它可能从根本上改变代理的基础执行方式 41。

| 记忆形态分类 | 心理学定义与功能特性 | 在大语言模型与认知代理架构中的典型实现 | 检索策略与应用偏好 |
| :---- | :---- | :---- | :---- |
| **工作记忆 (Working)** | 维持在意识中用于即时计算的暂态活跃信息。 | 上下文窗口(Context Window)内的系统提示、当前多轮对话记录。 | 无需外部检索，随Token滚动直接计算，受制于上下文窗口长度。 |
| **情景记忆 (Episodic)** | 带有明确时间戳和空间背景的自传体个人经历事件流。 | 向量数据库(Vector DB)存储的带时间元数据的观测日志和交互转录。 | 强调高精度(Precision)，强依赖时间过滤、角色匹配与语义相似度联合检索。 |
| **语义记忆 (Semantic)** | 抽象化的事实、常识、知识体系及稳定的自我认同观念。 | 结构化数据库与向量化概念嵌入(Concept Embeddings)的结合体。 | 强调高召回率(Recall)，基于概念联想和本体论扩展进行广泛匹配。 |
| **过程记忆 (Procedural)** | 执行技能、操作流程以及“如何做”的隐性知识网络。 | 大模型自身参数权重(隐性)，代理的外部硬编码工作流脚本或状态机(显性)。 | 直接触发调用，或通过相似任务检索以匹配最佳的执行函数与工具。 |

### **记忆检索机制的数学建模与多级反思架构**

在模拟具有数十年生活经验的人类个体时，其累积的记忆流庞大且充满冗余。如果在进行行为预测时将所有相关的历史事件未经筛选地注入上下文，必然会导致严重的上下文污染、推断延迟升高以及注意力发散。因此，个体画像的动态注入过程，极端依赖一套精细化的启发式记忆评估与检索算法。  
在被广泛引用的斯坦福生成式代理研究体系中，单条记忆对象的检索优先级评分被严格定义为三个独立标量的加权线性组合：近期性（Recency）、重要性（Importance）与相关性（Relevance） 37。近期性通常通过一个指数衰减函数来实现，确保越新近的观察日志权重越高；重要性函数则利用大语言模型的自然语言理解能力，在事件发生被录入时即刻对该事件的心理冲击力与生命意义进行从1到10级的数值打分（例如，一次日常的喝水可能被评为1分，而遭遇亲人变故或失业则被评为9或10分）；相关性则通过计算当前触发事件查询向量与历史记忆向量的余弦相似度（Cosine Similarity）来动态获得 37。  
为了实现更高阶的行为预测和目标规划，仅仅依靠离散底层的观察记忆是远远不够的。因此，高级代理架构中必须内置反思模块（Reflection Module） 37。系统会持续监听近期记忆记录。当近期新入库记忆的“重要性得分”总和跨越系统预设的阈值时，代理会被自动唤醒执行反思周期：它会首先从记忆流中调取最近发生的最具代表性的上百条记忆片段，向大语言模型发出提示，要求其提炼出若干个高层次的统摄性问题（Salient Questions）；随后，代理带着这些问题再次深入记忆海洋进行二次穿梭检索，并将获取的素材综合研判，生成多个具有深刻洞察力的新颖结论（Novel Insights） 45。这些经过高度抽象反思产生的高级节点，将被贴上“反思”标签，以新记忆的身份回填至记忆流网络中。正是由于这种从具体情境中提取抽象规律的内省能力，代理才能够在面对一份其历史上从未做过的社会科学量表时，依然能够依据其抽象化后的底层价值观体系，做出完全符合该真实人类底层人设的判断与答复。

### **动态知识图谱与复合记忆表示：跨越非结构化屏障的AriGraph与KnoBuilder范式**

虽然基于向量相似度的非结构化记忆检索取得了巨大的成功，但它在应对需要多步逻辑推导、长时间跨度下的因果溯源以及防止逻辑自相矛盾等复杂任务时，依然面临严重的性能瓶颈和“幻觉”挑战。为了彻底突破这一天花板，人工智能前沿探索将目光投向了图论。研究者们提出了一种将记忆结构化、图谱化的划时代方案，典型的代表包括AriGraph (Ariadne's Graph) 框架与KnoBuilder智能体环路机制 47。  
在AriGraph架构中，系统通过构建一个随环境探索动态扩张的认知网络，实现了对语义记忆与情景记忆的统一图谱化封装 49。在这个特殊的内存数据结构中，图谱的节点（Vertices）代表着抽象的语义实体（如某个具体的物品、地标概念、或是特定的人物社会关系），而那些随时间流逝发生的情景记忆，则被精妙地转化为连接或跨越这些语义节点的“情景边（Episodic Edges）”或是衍生的时间轴情景节点 49。这意味着，当代理被置于一个复杂的测试环境中时，它不再像传统RAG技术那样在毫无拓扑关联的海量文本碎片中盲目捞针，而是沿着结构严密的知识图谱网络，根据拓扑连通性进行理性的多跳游走与逻辑演绎 49。实证评估表明，这种整合了语义与情景的结构化记忆模式，极大地提升了大型语言模型代理在如文字游戏寻宝、复杂环境探索等长周期决策任务中的表现，显著压倒了传统的强化学习基线模型和简单的全文历史检索方法 49。  
与之形成呼应的KnoBuilder范式，则在个性化知识图谱的自动构建上提供了策略性支撑 47。面对杂乱无章的非结构化人类生活史文本记录，KnoBuilder实施了一套包括战略知识规划、自我优化与细化的多阶段信息验证，以及维护图结构逻辑连贯性的动态整合（Dynamic Consolidation）在内的闭环流转机制 47。这些机制有力地确保了被构建的个人画像在长期的信息摄入过程中不仅不会发生内在信仰与逻辑上的矛盾崩溃，还能实现对异常数据的有效修正。在这样的高维架构支撑下，代理的上下文空间所承载的，早已不再是扁平的特征标签列表或静止的字符串序列，而是一个不断呼吸、生长、具备自我修正能力的微型人类精神拓扑网络。

## **第三部分：行为决策的认知演算与情感约束机制**

当代理装备了精细的人格理论框架并被赋予了图谱化的记忆网络后，要想真正惟妙惟肖地预测人类，接下来必须解决一个核心的执行逻辑难题：如何在大模型的推理过程中复刻人类固有的认知局限性、非理性的冲动以及情感波动？纯粹理性和追求算力极致的大型语言模型在模拟真实人类时，常常会表现得“过于理性”、“逻辑过分完美且不知疲倦”。但我们深知，真实的血肉之躯在现实世界中的决策，常常是充满偏见、过度依赖直觉且随时受到情绪海啸裹挟的。

### **启发式直觉与深度逻辑审思：系统1与系统2的动态阈值切换**

认知心理学家、诺贝尔经济学奖得主丹尼尔·卡尼曼（Daniel Kahneman）在其经典的“双系统理论”（Dual-Process Theory）中提出，人类大脑中的认知加工过程可被分为两种截然不同的运作机制：系统1（System 1）与系统2（System 2） 53。系统1是极其快速、自动化、毫不费力且严重依赖直觉和历史经验启发式的；而系统2则是相对缓慢、需要高度集中注意力、进行深思熟虑的逻辑推演和代价高昂的理性计算 54。目前大语言模型的概率输出机制，天然地更类似于快速非迭代的系统1；而诸如思维链（Chain-of-Thought, CoT）等复杂提示策略，则是通过拉长推理步骤在强制模仿系统2的运作 54。  
为了在代理中逼真地模拟人类个体，画像中必须包含一组用于触发这两种不同系统动态切换的阈值参数和环境变量监听器。研究表明，在模拟环境中，通过引入“时间压迫感”、“任务信息错综复杂程度”以及“被试者当前处于剧烈的情绪波动状态中”等特征变量，可以有效地改变大模型分配给系统1与系统2的计算权重 53。  
当系统特意增加“认知负载（Cognitive Load）”时，模型将更容易依赖系统1的直觉响应。此时，代理会表现出一系列与真实人类在疲惫、紧张压力下高度吻合的“认知偏差（Cognitive Biases）” 53。例如，在期望效用理论框架的测试下，处于高认知负载或模拟负面情绪上下文中的大模型，会更加凸显出人类特有的风险厌恶（Risk Aversion）、损失厌恶倾向以及面对极小概率事件时的概率过度加权现象 54。此外，对自身能力缺乏认知的邓宁-克鲁格效应（Dunning-Kruger Effect）亦会在代理缺乏环境反馈校准时自发涌现 56。因此，要实现良好的预测，不仅要预测对象在理想状态下的最佳选择，更要预测其在认知资源匮乏时的偏倚反应。

### **情感计算环路与认知评估理论（EMA）**

情绪绝对不仅是人类行为的被动副产品，它在本质上是重塑人类决策优先级和行为方向的核心计算引擎。在现代代理架构设计中，若要突破僵化的文本匹配，必须在预测环路中引入严格的情绪反馈机制。这就不得不依托心理学中的认知评估理论（Cognitive Appraisal Theory, 常常在计算模型中被缩写为EMA架构） 28。  
EMA理论的核心主张是，情绪并非凭空产生或由刺激直接触发，情绪的本质是个体不断评估自身与周围环境关系的过程中产生的主观体验结果。这种评估关注事件是否阻碍或促进了自身的根本目标（目标相关性），事件是谁导致的（因果责任），以及个体在当前状态下拥有何种级别的可用应对资源潜力（Coping Potential） 57。在评估机制中，大语言模型代理利用其强大的模式识别和关联记忆提取能力，迅速扫视并评估眼前的挑战与自身的记忆图谱及设定的深层动机（例如SDT框架下的自主性需求）的兼容性。如果发现新事件严重侵犯了其内设的核心生命叙事，则评估模块将被激活并产生高强烈的情绪冲突信号。  
落实在具体的工程实现框架中，例如EmoACT（情感控制理论的计算平台），系统拒绝将情绪简单粗暴地贴上“悲伤”、“愤怒”的离散标签分类，而是创新性地将情感建模为一个在“评估-潜能-活动”（Evaluation-Potency-Activity, EPA）三维连续向量空间中的复杂微积分演化过程 58。在更高阶的设计中，引入了“情绪链（Chain-of-Emotion）”架构。在这个精密环路中，当来自用户或环境的输入信息被载入系统并储存于记忆库时，该动作本身会直接触发一个独立的内部Appraisal评估调用。评估结果不仅使得代理当下的输出文字携带特定的语调甚至情绪失控的断句特征，更重要的是，这份“因为遭遇某事而产生的特定情绪评估档案”本身也会作为新的特殊情景记忆被重新封存入底层架构中，影响未来对相似事件的情绪定调 59。通过强化学习算法与自我和元评估相结合，代理能够越来越熟练地利用大模型的常识推理，像真人一样在复杂对话场景中演绎出合乎情理的情绪起伏转换规律 60。

### **躯体标记假说（Somatic Marker Hypothesis）在人工智能中的映射**

为了进一步彻底弥补数字网络中冰冷的逻辑代码与生物神经系统基于直觉的情感判断之间的巨大鸿沟，神经生物学家安东尼奥·达马西奥（Antonio Damasio）提出的躯体标记假说（Somatic Marker Hypothesis, SMH）为人工智能行为预测提供了一块决定性的拼图 61。  
躯体标记假说源于对腹内侧前额叶皮层（vmPFC）受损患者的深度临床观察。这些患者虽然在智商测验、语言逻辑及记忆力等传统的冷认知指标上一切正常，但在现实生活中处理风险、做出长期有利决策的能力却遭遇了灾难性溃败 61。原因在于，脑部损伤切断了他们大脑利用过往负面经历在生理上唤起的微弱且快速的“不适躯体标记”（如心跳加速、轻微的恶心或肌肉紧绷的先兆）。失去这种无意识的生物学直觉警告，患者在面对选择时，被迫对每一个可能的分支选项进行极其缓慢、繁重且永无止境的逻辑成本效益计算分析，最终导致决策瘫痪或频繁做出高风险灾难性选择 61。著名的“爱荷华赌博任务”（Iowa Gambling Task）实验中，健康个体在意识到哪副牌是危险的之前，其皮肤电导反应（SCR）就已经出现了显著的“预期性飙升”，而vmPFC患者则丧失了这种情绪防线 61。  
将这一具有生物学深刻洞见的假说引入认知人工智能领域，能够显著提升模拟的仿真程度。既然基于硅基的AI系统不可能拥有产生真实心率和胃部痉挛的血肉之躯，前沿探索便致力于为其打造一种“人工躯体标记（Artificial Somatic Markers）”算法机制 62。在该机制下，当代理利用内部机制检索到当前情境的特征向量与历史记忆中导致严重失败、受挫或强负面情绪反馈的情境呈现出高度数学相似性时，系统并非调用大语言模型的逻辑链要求其详细分析风险原因，而是人为地在推理生成前的大模型隐层激活路径或提示词约束中，注入一个表征强烈“高风险规避直觉预警”的沉重惩罚权重或先验偏见。这种人工神经阻断机制强行跳过了那些繁琐、高度消耗算力且看似合乎逻辑的全面评估，直接迫使代理基于经验的情感直觉，在潜意识层面迅速否定危险选项。通过模拟这种机制，AI代理能够极其逼真地再现真实人类那种基于有限经验的、“不可言传的第六感直觉”、以及非理性但高效的经验规避行为 62。

## **第四部分：Profile的工程化注入与模型引导控制范式**

在确立了由多层次特质、需求动机、图谱化记忆流网络以及情感直觉演算系统共同交织而成的心理学庞大骨架之后，摆在研究者面前最艰巨的技术挑战是：如何以一种工程化、低延迟且可精确控制计算成本的方式，将这一庞大且多维的人类画像“压缩”并“注入”到大型语言模型有限的上下文窗口中，并在长时间序列的动态社会交互中实施有效的人格特征引导。

### **深度定性访谈转录与多领域专家反思抽取的合成机制：以千人仿真为例**

在关于如何构建高保真画像的探索中，斯坦福大学等顶尖研究机构开展的“1,000人生成式Agent模拟实验”奠定了一个具有里程碑意义的工业级实践标准 1。该项宏大的研究彻底摒弃了以往使用简单文本字典描述人口统计学标签（如“一名居住在得克萨斯州的35岁中产阶级白人共和党男性”）的基线做法，因为大量研究证实此类扁平化做法极易触发大模型内置训练集中对政治阵营、种族及社会阶层的严重系统性偏见预设，导致结果失真 5。  
构建极其拟真的底层画像范式需经历以下精密环节： 首先是深度原材料的挖掘。研究团队利用集成了高级语音能力的GPT-4模型系统作为自动化采访官，对超过一千名具有多样化背景的真实人类志愿者进行了平均长达两个小时的深度、半结构化定性访谈（访谈协议参考自社会科学中著名的美国之声项目，涵盖个人生命史重大转折、对各种社会现实问题的多维看法等），从而积累下极其丰富且保留了浓郁个体语言色彩的数十万字规模访谈逐字稿记录 1。 其次，这些转录文本并非被原封不动地全量输入模型，而是经过时间线切片处理后被录入架构的长期底层记忆流中 67。 最为核心的技术飞跃在于引入了“多专家视角的反思抽象提取机制（Multi-Expert Reflection）”。为了让代理具备回答那些并未在访谈中被明确问及的社会现象和宏大问题的泛化迁移能力，系统调度后台大模型，要求其分别扮演四种不同学科背景的社会科学界顶级领域专家（具体包括：临床心理学家、行为经济学家、政治决策分析师以及人口社会学家） 6。大模型以专家的严密逻辑对同一份个人访谈逐字稿进行交叉透视与综合审阅，并各自出具一份提炼了该个体特定领域潜在信念、行为规律和深层价值观念的“反思合成档案” 6。 最后，动态上下文精准注入。在模拟实验执行阶段，当系统需要预测特定代理对一份综合社会调查（GSS）问卷或实验选择的反应时，系统前端的分类器会首先预判当前面临的问题最贴近哪一个“专家评估域”的知识。随后，将经过精心挑选和时间过滤的核心访谈原始文本对话切片，连同该特定领域专家所做的高阶反思报告一并提取出来，动态合成入最终的提示词注入模板中 1。这一极其复杂的系统工程，在面对预测未经训练的广泛议题时，达成了高达85%的人类一致性行为预测匹配率，充分证明了“深度定性真实文本切片 \+ 结构化多专家反思引擎”是将个人历史平稳映射进AI大脑的黄金实现范式 1。

### **情境感知的人格引导与特征层控制：IRiS框架的微操技术**

尽管利用详尽的上下文窗口注入能够极大地丰富代理的背景知识，但在长文本推理运算中，大模型本身为了维持自然语言文本生成的流畅性，依然存在“注意力漂移”现象，或者在处理含有强烈误导性暗示的复杂测试情境时，不自觉地退回到其默认的“无害且平庸的AI助手”模式，从而偏离设定的人类画像。为了从模型推理的深层架构上强行保证性格特质输出的钢铁一致性，前沿技术界开始转向更底层的表征工程（Representation Engineering）。在这其中，能够感知情境的情境人格控制框架——**IRiS (Identify-Retrieve-Steer，即识别-检索-引导框架)** 提供了一种无须耗时且破坏模型通用能力进行微调（Training-free）的精锐底层注入控制方案 17。  
由于特定的性格特质组合（诸如大五人格的量表极值表现、或者是特定研究环境下的“阿谀奉承倾向”、“反叛心理”甚至“易产生幻觉倾向”等）在大型语言模型训练后，往往被隐秘地编码存在于特定层的隐藏状态向量空间中（这些隐层节点被称为 Persona Neurons 或人格向量） 14。IRiS框架的执行流可以被解构为三个连续的微操相位： 第一步，识别（Identify）相位。在脱机预处理阶段，技术人员利用探针和差异化激活测试，精准且细致地定位出那些控制特定情境化人设响应模式的“人格神经元”，并从庞杂的网络中提取出隐藏层向量分布中低秩且高度关联共享的核心特征子空间地图 17。 第二步，检索（Retrieve）相位。系统上线运行后，IRiS框架部署了一个高度敏锐的情境感知组件。当探测到当前输入的新上下文，该组件会与代理画像中的先验特征预设以及历史讨论话题库进行联合比对分析，研判当前场景对个体性格的暴露需求程度 68。 第三步，引导（Steer）相位。这是最核心的控制动作。基于前期的相似度评估指标，系统在模型生成回答的推理过程中，实行动态的层级选择和精确制导。通过在目标特征隐空间的特定轴向上施加基于相似度权重的微弱干扰力（Perturbations）与放大缩放调节（Scaling），系统强制干预并放大特定神经元的激活值电平。这种在模型内部进行的外科手术式微调，能够在绝不破坏大模型原有的语言流畅性连贯性、回答逻辑方差以及其通用的基础功能的前提下，强硬地在输出结果中彰显出与底层画像绝对吻合的鲜明性格特征，成功跨越了心理学抽象理论到实用机器学习模型特征对齐工程应用之间的巨大技术鸿沟 17。在专门用于评估情境化人格一致性的新一代复杂基准测试集（如SPBench等）上，配备了该引擎的代理大幅度超越了目前现有的所有基线方案 17。

### **认知架构闭环下的自主生态演化模型**

当所有上述心理模型参数化理论、庞大的记忆管理网络技术以及精妙的注入控制范式被集成于单一代理实例之中时，代理对人类行为的预测能力便不再是简单的问答式反馈，而是构成了一个具有强大自我演进动力的“观察-评估-同化-反应”闭环生态系统。  
在一个标准的预测执行周期内，当外界环境发出刺激信号（如一句挑衅的言语挑战、或是测试中呈现的一份量表），该事件立刻映射至代理的AriGraph图谱网络表面，引发拓扑节点的连锁共振激活，调动出相关的情景与语义深层记忆 49。与此同时，通过角色身份激活（RIA）管道，个体画像中特定的认知情感单元（CAUs）被深度唤醒，明确其目标网络与依恋关系防线状态 22。紧接着，元系统计算当前的认知负载水平，并裁决是触发系统1的直觉偏差还是系统2的理性推演，期间伴随着EMA情绪链对事态潜能的动态评估与躯体标记发出的人工生理直觉警报 53。最后，伴随着底层神经元表征的精确微观引导（IRiS系统控制），大型语言模型顺利输出极其精准贴合角色性格逻辑的行为动作或语言回复 68。而这一连串内部剧烈激荡的交互动作及其产生的影响，又会被即刻作为最新的情景节点转译回填至记忆图谱之中，进而不断逼近反思阈值的临界点，引发新的高阶思想涌现，推动个体画像中“自我同一性”连贯且永不停歇地生长与演进 37。

## **结论**

在认知科学、神经生物机制与心理学深度交叉的前沿视角下，为大型语言模型构筑用以执行高频度、高逼真人类行为预测的代理画像（Profile），已经全面而彻底地超越了早期依赖字典标签进行静态系统提示语拼接的简陋时代。这一系统工程在本质上是利用机器智能的软硬件底层架构，在硅基网络中全方位地复刻人类的心理与神经构造学模型。  
人格与特质的表征建构，必须倚靠麦克亚当斯的严谨三层理论框架，辅以米歇尔的认知情感系统（CAPS）等，从而赋予代理在特定情境暴露下跨越静态标签束缚的动态适应能力和稳定的内部动机工作模式；信息与认知的留存架构，早已宣判了孤立且无历史维度上下文窗口的失败，取而代之的，是诸如AriGraph般能够将无形语义概念与极具时序价值的情景事件在立体图谱中完美交融的高维动态记忆网络，并叠加具有高度学科专业视角的结构化反思引擎；在决策机制的重塑上，通过在模型中人为设置系统1与系统2切换阈值、内嵌EMA情绪连续演化微积分环路以及借由人工躯体标记机制重现生理预警直觉，代理才得以摆脱超强算力带来的“过度理性计算”陷阱，逼真地再现人类在复杂社会压力环境中的非理性认知偏差。而所有这些辉煌的抽象理论设计，最终都有赖于定性深度长时访谈转录的材料支撑，以及基于底层神经网络隐式空间特征放大、无损注入引导等表征工程技术落地生根。  
展望未来，这种完美熔接了复杂人类心理学宏大架构与图谱网络进化技术的代理范式，必将以前所未有的革命性力量，深刻推动包括宏观社会经济政策的仿真推演演习、微观复杂消费行为心理学实验预测、乃至个性化数字精神干预陪伴治疗在内的诸多深水区应用。人工智能也正是在这一历史进程中，褪去纯粹统计学概率预测的冰冷外衣，大踏步迈向具备高度拟人连贯性、甚至孕育出虚拟个体心理实体的新纪元。

#### **引用的著作**

1. Simulating Human Behavior with AI Agents | Stanford HAI, [https://hai.stanford.edu/policy/simulating-human-behavior-with-ai-agents](https://hai.stanford.edu/policy/simulating-human-behavior-with-ai-agents)  
2. The drive to simulate human behaviour in AI agents \- Hello Future, [https://hellofuture.orange.com/en/the-drive-to-simulate-human-behaviour-in-ai-agents/](https://hellofuture.orange.com/en/the-drive-to-simulate-human-behaviour-in-ai-agents/)  
3. Simulating Human Behavior with AI Agents \- Stanford HAI, [https://hai.stanford.edu/assets/files/hai-policy-brief-simulating-human-behavior-with-ai-agents.pdf](https://hai.stanford.edu/assets/files/hai-policy-brief-simulating-human-behavior-with-ai-agents.pdf)  
4. (PDF) Generative Agent Simulations of 1000 People (2024) | Joon Sung Park \- SciSpace, [https://scispace.com/papers/generative-agent-simulations-of-1000-people-31sj9byjex26](https://scispace.com/papers/generative-agent-simulations-of-1000-people-31sj9byjex26)  
5. Generative Agent Simulations of 1,000 People | Request PDF \- ResearchGate, [https://www.researchgate.net/publication/385899321\_Generative\_Agent\_Simulations\_of\_1000\_People](https://www.researchgate.net/publication/385899321_Generative_Agent_Simulations_of_1000_People)  
6. Generative Agent Simulations of 1000 People \- FrankonFraud, [https://frankonfraud.com/wp-content/uploads/2024/11/AI-Cloning.pdf](https://frankonfraud.com/wp-content/uploads/2024/11/AI-Cloning.pdf)  
7. LLM Nepotism in Organizational Governance \- arXiv, [https://arxiv.org/pdf/2604.09620](https://arxiv.org/pdf/2604.09620)  
8. Generative Agent Simulations of 1,000 People \- Hugging Face, [https://huggingface.co/blog/mikelabs/generative-agent-simulations-1000-people](https://huggingface.co/blog/mikelabs/generative-agent-simulations-1000-people)  
9. Judging with Personality and Confidence: A Study on Personality-Conditioned LLM Relevance Assessment \- arXiv, [https://arxiv.org/html/2601.01862v1](https://arxiv.org/html/2601.01862v1)  
10. Social-Cognitive Theory of Personality Assessment | Request PDF \- ResearchGate, [https://www.researchgate.net/publication/247562631\_Social-Cognitive\_Theory\_of\_Personality\_Assessment](https://www.researchgate.net/publication/247562631_Social-Cognitive_Theory_of_Personality_Assessment)  
11. Moral Foundations Theory: The Pragmatic Validity of Moral Pluralism \- CDN, [https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/1/863/files/2020/06/Graham-et-al-2013.AESP\_.pdf](https://bpb-us-e2.wpmucdn.com/sites.uci.edu/dist/1/863/files/2020/06/Graham-et-al-2013.AESP_.pdf)  
12. PROFESSIONAL SOCIALIZATION OF ENGINEERS: MORAL FORMATION AND ORGANIZATIONAL CULTURE \- Purdue University Graduate School research repository, [https://hammer.purdue.edu/ndownloader/files/36467112](https://hammer.purdue.edu/ndownloader/files/36467112)  
13. Hierarchical Systems of Personality Traits | PDF | Affect (Psychology) \- Scribd, [https://www.scribd.com/document/846564283/Journal-of-Personality-2017-Fajkowska-Personality-Traits-Hierarchically-Organized-Systems](https://www.scribd.com/document/846564283/Journal-of-Personality-2017-Fajkowska-Personality-Traits-Hierarchically-Organized-Systems)  
14. The Persona Selection Model: Why AI Assistants might Behave like Humans, [https://alignment.anthropic.com/2026/psm/](https://alignment.anthropic.com/2026/psm/)  
15. Patterns, Not People: Personality Structures in LLM-powered Persona Agents, [https://cetas.turing.ac.uk/publications/patterns-not-people-personality-structures-llm-powered-persona-agents](https://cetas.turing.ac.uk/publications/patterns-not-people-personality-structures-llm-powered-persona-agents)  
16. Designing AI-Agents with Personalities: A Psychometric Approach \- arXiv, [https://arxiv.org/html/2410.19238v3](https://arxiv.org/html/2410.19238v3)  
17. Beyond Static Personas: Situational Personality Steering for Large Language Models, [https://www.researchgate.net/publication/403868311\_Beyond\_Static\_Personas\_Situational\_Personality\_Steering\_for\_Large\_Language\_Models](https://www.researchgate.net/publication/403868311_Beyond_Static_Personas_Situational_Personality_Steering_for_Large_Language_Models)  
18. Joy as a Virtue: The Means and Ends of Joy \- ResearchGate, [https://www.researchgate.net/publication/338659998\_Joy\_as\_a\_Virtue\_The\_Means\_and\_Ends\_of\_Joy](https://www.researchgate.net/publication/338659998_Joy_as_a_Virtue_The_Means_and_Ends_of_Joy)  
19. Beyond Static Personas: Situational Personality Steering for Large Language Models \- arXiv, [https://arxiv.org/html/2604.13846v2](https://arxiv.org/html/2604.13846v2)  
20. Personality as a Dynamical System: Emergence of Stability and Distinctiveness from Intra- And Interpersonal Interactions | Request PDF \- ResearchGate, [https://www.researchgate.net/publication/247759672\_Personality\_as\_a\_Dynamical\_System\_Emergence\_of\_Stability\_and\_Distinctiveness\_from\_Intra-\_And\_Interpersonal\_Interactions](https://www.researchgate.net/publication/247759672_Personality_as_a_Dynamical_System_Emergence_of_Stability_and_Distinctiveness_from_Intra-_And_Interpersonal_Interactions)  
21. (PDF) Personality Dynamics \- ResearchGate, [https://www.researchgate.net/publication/354251042\_Personality\_dynamics](https://www.researchgate.net/publication/354251042_Personality_dynamics)  
22. Thinking in Character: Advancing Role-Playing Agents with Role-Aware Reasoning, [https://openreview.net/forum?id=geNdDlzKTG\&referrer=%5Bthe%20profile%20of%20Tiejun%20Zhao%5D(%2Fprofile%3Fid%3D\~Tiejun\_Zhao1)](https://openreview.net/forum?id=geNdDlzKTG&referrer=%5Bthe+profile+of+Tiejun+Zhao%5D\(/profile?id%3D~Tiejun_Zhao1\))  
23. Toward a unified theory of personality: Integrating dispositions and processing dynamics within the cognitive-affective processing system | Request PDF \- ResearchGate, [https://www.researchgate.net/publication/232582450\_Toward\_a\_unified\_theory\_of\_personality\_Integrating\_dispositions\_and\_processing\_dynamics\_within\_the\_cognitive-affective\_processing\_system](https://www.researchgate.net/publication/232582450_Toward_a_unified_theory_of_personality_Integrating_dispositions_and_processing_dynamics_within_the_cognitive-affective_processing_system)  
24. Handbook of Self-Regulation \- National Academic Digital Library of Ethiopia, [https://ndl.ethernet.edu.et/bitstream/123456789/28342/1/162.pdf.pdf](https://ndl.ethernet.edu.et/bitstream/123456789/28342/1/162.pdf.pdf)  
25. Representation of knowledge-and-appraisal personality architecture... \- ResearchGate, [https://www.researchgate.net/figure/Representation-of-knowledge-and-appraisal-personality-architecture-KAPA-mechanisms\_fig2\_8890988](https://www.researchgate.net/figure/Representation-of-knowledge-and-appraisal-personality-architecture-KAPA-mechanisms_fig2_8890988)  
26. Personality Processes: Mechanisms by which Personality Traits “Get Outside the Skin” \- PMC, [https://pmc.ncbi.nlm.nih.gov/articles/PMC3193854/](https://pmc.ncbi.nlm.nih.gov/articles/PMC3193854/)  
27. Using a Knowledge-and-Appraisal Model of Personality Architecture to Understand Consistency and Variability in Smokers' Self-Efficacy Appraisals in High-Risk Situations \- ResearchGate, [https://www.researchgate.net/publication/6421547\_Using\_a\_knowledge-and-appraisal\_model\_of\_personality\_architecture\_to\_understand\_consistency\_and\_variability\_in\_smokers'\_self-efficacy\_appraisals\_in\_high-risk\_situations](https://www.researchgate.net/publication/6421547_Using_a_knowledge-and-appraisal_model_of_personality_architecture_to_understand_consistency_and_variability_in_smokers'_self-efficacy_appraisals_in_high-risk_situations)  
28. AgentSociety: Large-Scale Simulation of LLM-Driven Generative Agents Advances Understanding of Human Behaviors and Society \- arXiv, [https://arxiv.org/html/2502.08691v1](https://arxiv.org/html/2502.08691v1)  
29. Self-Determination Theory and Workplace Outcomes: A Conceptual Review and Future Research Directions \- MDPI, [https://www.mdpi.com/2076-328X/14/6/428](https://www.mdpi.com/2076-328X/14/6/428)  
30. Maslow ' s hierarchy of needs. | Download Scientific Diagram \- ResearchGate, [https://www.researchgate.net/figure/Maslow-s-hierarchy-of-needs\_fig1\_249322072](https://www.researchgate.net/figure/Maslow-s-hierarchy-of-needs_fig1_249322072)  
31. Designing Conversational Agents: A Self-Determination Theory Approach \- selfdeterminationtheory.org, [https://selfdeterminationtheory.org/wp-content/uploads/2021/05/2021\_YangAurisicchio\_DesigningConversational.pdf](https://selfdeterminationtheory.org/wp-content/uploads/2021/05/2021_YangAurisicchio_DesigningConversational.pdf)  
32. Assumptions about Human Motivation have Consequences for Practice \- selfdeterminationtheory.org, [https://selfdeterminationtheory.org/wp-content/uploads/2024/06/InPress\_GagneHewett\_Assumptions.pdf](https://selfdeterminationtheory.org/wp-content/uploads/2024/06/InPress_GagneHewett_Assumptions.pdf)  
33. Trust, Anxious Attachment, and Conversational AI Adoption Intentions in Digital Counseling: A Preliminary Cross-Sectional Questionnaire Study \- PMC, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12056427/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12056427/)  
34. Chatting Up Attachment: Using LLMs to Predict Adult Bonds \- ResearchGate, [https://www.researchgate.net/publication/383701169\_Chatting\_Up\_Attachment\_Using\_LLMs\_to\_Predict\_Adult\_Bonds](https://www.researchgate.net/publication/383701169_Chatting_Up_Attachment_Using_LLMs_to_Predict_Adult_Bonds)  
35. Synthesizing Bonds: Enhancing Adult Attachment Predictions with LLM-Generated Data, [https://openreview.net/forum?id=8WpRt9pjeh](https://openreview.net/forum?id=8WpRt9pjeh)  
36. Structure Matters: Evaluating Multi-Agents Orchestration in Generative Therapeutic Chatbots, [https://arxiv.org/html/2603.00774v2](https://arxiv.org/html/2603.00774v2)  
37. Generative Agents \- LukeW, [https://www.lukew.com/ff/entry.asp?2030](https://www.lukew.com/ff/entry.asp?2030)  
38. \[2304.03442\] Generative Agents: Interactive Simulacra of Human Behavior \- arXiv, [https://arxiv.org/abs/2304.03442](https://arxiv.org/abs/2304.03442)  
39. An architectural framework for Generative Agents | by Daniele Nanni \- Medium, [https://medium.com/@daniele.nanni/from-npcs-to-generative-agents-part-2-d09d3af37738](https://medium.com/@daniele.nanni/from-npcs-to-generative-agents-part-2-d09d3af37738)  
40. What Is Agent Memory? A Guide to Enhancing AI Learning and Recall | MongoDB, [https://www.mongodb.com/resources/basics/artificial-intelligence/agent-memory](https://www.mongodb.com/resources/basics/artificial-intelligence/agent-memory)  
41. Cognitive Architectures for Language Agents \- arXiv, [https://arxiv.org/html/2309.02427v3](https://arxiv.org/html/2309.02427v3)  
42. AI agent memory: Building stateful AI systems \- Redis, [https://redis.io/blog/ai-agent-memory-stateful-systems/](https://redis.io/blog/ai-agent-memory-stateful-systems/)  
43. Memory for agents \- LangChain, [https://www.langchain.com/blog/memory-for-agents](https://www.langchain.com/blog/memory-for-agents)  
44. Agentic AI memory management with Elasticsearch, [https://www.elastic.co/search-labs/blog/ai-agent-memory-management-elasticsearch](https://www.elastic.co/search-labs/blog/ai-agent-memory-management-elasticsearch)  
45. A Deep Dive Into LangChain's Generative Agents | blog\_posts – Weights & Biases \- Wandb, [https://wandb.ai/vincenttu/blog\_posts/reports/A-Deep-Dive-Into-LangChain-s-Generative-Agents--Vmlldzo1MzMwNjI3](https://wandb.ai/vincenttu/blog_posts/reports/A-Deep-Dive-Into-LangChain-s-Generative-Agents--Vmlldzo1MzMwNjI3)  
46. Generative Agents: Interactive Simulacra of Human Behavior \- 3D Virtual and Augmented Reality, [https://3dvar.com/Park2023Generative.pdf](https://3dvar.com/Park2023Generative.pdf)  
47. KnoBuilder: An LLM-Agent for Autonomous and Personalized Knowledge Graph Construction from Unstructured Text \- NeurIPS 2026, [https://neurips.cc/virtual/2025/129837](https://neurips.cc/virtual/2025/129837)  
48. \[Regular\] KnoBuilder: An LLM-Agent for Autonomous and Personalized Knowledge Graph Construction from Unstructured Text | OpenReview, [https://openreview.net/forum?id=teewCPCv2m](https://openreview.net/forum?id=teewCPCv2m)  
49. AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents \- IJCAI, [https://www.ijcai.org/proceedings/2025/0002.pdf](https://www.ijcai.org/proceedings/2025/0002.pdf)  
50. AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents \- SciSpace, [https://scispace.com/pdf/arigraph-learning-knowledge-graph-world-models-with-episodic-xvgwvwiylh.pdf](https://scispace.com/pdf/arigraph-learning-knowledge-graph-world-models-with-episodic-xvgwvwiylh.pdf)  
51. AriGraph: Learning Knowledge Graph World Models with Episodic, [https://www.alphaxiv.org/overview/2407.04363v1](https://www.alphaxiv.org/overview/2407.04363v1)  
52. AIRI-Institute/AriGraph \- GitHub, [https://github.com/AIRI-Institute/AriGraph](https://github.com/AIRI-Institute/AriGraph)  
53. Emulating Aggregate Human Choice Behavior and Biases with GPT Conversational Agents, [https://arxiv.org/html/2602.05597v1](https://arxiv.org/html/2602.05597v1)  
54. Towards Rationality in Language and Multimodal Agents: A Survey \- ACL Anthology, [https://aclanthology.org/2025.naacl-long.186.pdf](https://aclanthology.org/2025.naacl-long.186.pdf)  
55. (PDF) Emulating Aggregate Human Choice Behavior and Biases, [https://www.researchgate.net/publication/400505590\_Emulating\_Aggregate\_Human\_Choice\_Behavior\_and\_Biases\_with\_GPT\_Conversational\_Agents](https://www.researchgate.net/publication/400505590_Emulating_Aggregate_Human_Choice_Behavior_and_Biases_with_GPT_Conversational_Agents)  
56. ICML Poster Position: LLMs Need a Bayesian Meta-Reasoning Framework for More Robust and Generalizable Reasoning \- ICML 2026, [https://icml.cc/virtual/2025/poster/40142](https://icml.cc/virtual/2025/poster/40142)  
57. Sentipolis: Emotion-Aware Agents for Social Simulations \- arXiv, [https://arxiv.org/html/2601.18027v1](https://arxiv.org/html/2601.18027v1)  
58. EmoACT: Integrating Identity, Impression, and Emotion for Synthetic Affective Agent, [https://zenodo.org/records/17629714](https://zenodo.org/records/17629714)  
59. (PDF) An appraisal-based chain-of-emotion architecture for affective language model game agents \- ResearchGate, [https://www.researchgate.net/publication/380491672\_An\_appraisal-based\_chain-of-emotion\_architecture\_for\_affective\_language\_model\_game\_agents](https://www.researchgate.net/publication/380491672_An_appraisal-based_chain-of-emotion_architecture_for_affective_language_model_game_agents)  
60. A Third-Person Appraisal Agent: Learning to Reason About Emotions in Conversational Contexts | OpenReview, [https://openreview.net/forum?id=i6b2TrTNMz](https://openreview.net/forum?id=i6b2TrTNMz)  
61. Somatic marker hypothesis \- Wikipedia, [https://en.wikipedia.org/wiki/Somatic\_marker\_hypothesis](https://en.wikipedia.org/wiki/Somatic_marker_hypothesis)  
62. Somatic Marker Hypothesis \- The Decision Lab, [https://thedecisionlab.com/reference-guide/psychology/somatic-marker-hypothesis](https://thedecisionlab.com/reference-guide/psychology/somatic-marker-hypothesis)  
63. Testing the somatic marker hypothesis in decisions-from-experience with non-stationary outcome probabilities \- PMC, [https://pmc.ncbi.nlm.nih.gov/articles/PMC10419193/](https://pmc.ncbi.nlm.nih.gov/articles/PMC10419193/)  
64. The Somatic Marker Hypothesis and the Possible Functions of the Prefrontal Cortex \[and Discussion\] \- USC Institute for Creative Technologies, [https://people.ict.usc.edu/\~gratch/CSCI534/Readings/The%20Somatic%20Marker%20Hypothesis%20and%20the%20Possible%20Functions%20of%20the%20Prefrontal%20Cortex%20%5BandDiscussion%5D.pdf](https://people.ict.usc.edu/~gratch/CSCI534/Readings/The%20Somatic%20Marker%20Hypothesis%20and%20the%20Possible%20Functions%20of%20the%20Prefrontal%20Cortex%20%5BandDiscussion%5D.pdf)  
65. What is Agentic AI? \- Stanford HAI, [https://hai.stanford.edu/ai-definitions/what-is-agentic-ai](https://hai.stanford.edu/ai-definitions/what-is-agentic-ai)  
66. Generative Agent Simulations of 1000 People \- Synthetic Users, [https://www.syntheticusers.com/science-posts/generative-agent-simulations-of-1-000-people](https://www.syntheticusers.com/science-posts/generative-agent-simulations-of-1-000-people)  
67. \[Literature Review\] Generative Agent Simulations of 1,000 People \- Moonlight, [https://www.themoonlight.io/en/review/generative-agent-simulations-of-1000-people](https://www.themoonlight.io/en/review/generative-agent-simulations-of-1000-people)  
68. Beyond Static Personas: Situational Personality Steering for Large Language Models \- arXiv, [https://arxiv.org/html/2604.13846v1](https://arxiv.org/html/2604.13846v1)  
69. Zesheng Wei's research works \- ResearchGate, [https://www.researchgate.net/scientific-contributions/Zesheng-Wei-2347254481](https://www.researchgate.net/scientific-contributions/Zesheng-Wei-2347254481)  
70. Beyond Static Personas: Situational Personality Steering for Large Language Models \- arXiv, [https://arxiv.org/abs/2604.13846](https://arxiv.org/abs/2604.13846)  
71. Structured Personality Control and Adaptation for LLM Agents \- arXiv, [https://arxiv.org/html/2601.10025v1](https://arxiv.org/html/2601.10025v1)