// ═══════════════════════════════════════════════════════════════════════
// Demo Data — hardcoded project + analysis results for GitHub Pages demo
// ═══════════════════════════════════════════════════════════════════════

export const DEMO_PROJECT = {
  id: 'demo-project-001',
  name: '两室一厅装修方案分析',
  description: '这是一个装闭 AI 的 Demo 项目，展示了完整的装修陷阱分析流程。包含全屋定制报价与半包预算的交叉核查。',
  input_text: '两室一厅装修，预算20万，要求现代简约风格。业主特别强调：墙地面不做二遍防水处理，电线布线统一使用2.5平方多芯线。',
  image_count: 0,
  file_count: 2,
  status: 'completed' as const,
  created_at: '2026-01-15T10:30:00Z',
  updated_at: '2026-01-15T11:00:00Z',
}

export const DEMO_FILES = [
  {
    id: 'file-001',
    project_id: 'demo-project-001',
    filename: 'quotation.pdf',
    original_name: '全屋定制报价单.pdf',
    file_type: 'pdf' as const,
    file_size: 2840000,
    parsed_content: null,
    created_at: '2026-01-15T10:31:00Z',
  },
  {
    id: 'file-002',
    project_id: 'demo-project-001',
    filename: 'budget.pdf',
    original_name: '半包预算表.pdf',
    file_type: 'pdf' as const,
    file_size: 1650000,
    parsed_content: null,
    created_at: '2026-01-15T10:32:00Z',
  },
]

export const DEMO_IMAGES: any[] = []

export const DEMO_ANALYSIS_RESULT = {
  id: 'analysis-demo-001',
  project_id: 'demo-project-001',
  status: 'completed' as const,
  summary: {
    total_pitfalls: 11,
    critical_count: 2,
    high_count: 2,
    medium_count: 6,
    low_count: 1,
    score: 12,
    summary_text:
      '两份文件漏洞百出：爱格板门板+铝框玻璃门=视觉暴发户+清洁噩梦；岩板台面、层板灯、顶角石膏线全是加钱不加实用的"面子工程"；衣帽间背板单价虚高、折扣计算混乱，整体报价水分惊人。半包预算中防水、电线、角阀等多项与用户备注矛盾，疑似偷工减料或增项陷阱。',
  },
  pitfalls: [
    {
      id: '1',
      category: '其他',
      description: '衣帽间铝框玻璃门——贵得离谱的落灰神器',
      severity: 'high' as const,
      location: '全屋定制报价单-衣帽间（第七项）第8条',
      suggestion:
        '采用同色爱格板门板（报价520元/㎡）即可，3扇门可省约4000元。如需通透效果，可在局部做一扇玻璃门点缀，全做就是冤大头。',
      critique:
        '3扇铝框玻璃门（浅金色极窄铝框+欧茶玻璃）面积不足4㎡，单价高达1260元/㎡，总价5027元。玻璃门不仅贵，而且日常使用指纹、灰尘明显，内部衣物稍有不整即暴露无遗，沦为"展示柜"。对于衣帽间这种私密储物空间，纯粹是设计师为了拉高总价塞进来的"颜值陷阱"。',
      trap_explanation:
        '设计师利用业主对"轻奢""极窄边框"的追捧，推荐高利润的玻璃门，实际使用体验极差（指纹、落灰、隐私全无），且后期清洁维护成本高。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '2',
      category: '隐性成本',
      description: '全屋层板灯——为装饰而装饰的"光污染"',
      severity: 'medium' as const,
      location: '全屋定制报价单-客厅装饰柜（第8条）、鞋柜（第4条）、衣帽间（第12条）',
      suggestion:
        '取消所有非必要层板灯，仅保留衣帽间主通道或客厅展示区1-2根作为氛围灯即可，省下1000元以上。',
      critique:
        '共安装10根45度层板灯，每根145元，总价1450元。这些灯带在实际使用中几乎不会常开，尤其是鞋柜和衣柜内部，开门即亮灯的感应灯带除了增加电池更换成本和干扰视觉，毫无实际价值。客厅装饰柜的层板灯更是纯粹的装饰性照明，日常开启次数寥寥。',
      trap_explanation:
        '层板灯是定制行业的"标配增项"，单价不高但数量一多总价可观，实际使用率极低，属于"买了不用"的智商税。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '3',
      category: '隐性成本',
      description: '主卫岩板台面——脆弱的昂贵"面子"',
      severity: 'low' as const,
      location: '全屋定制报价单-主卫台盆柜（第六项）第3条',
      suggestion:
        '改用15mm石英石台面（同预算表中其他项目使用的石英石），节省约800元，且耐造。',
      critique:
        '仅1.17m长的台面竟选用单价1860元/m的岩板，总价2176元，比同长度石英石（1180元/m）贵了将近一倍。岩板虽然颜值高，但脆性大，受冲击易崩边，后期台盆安装、日常使用中稍有不慎便开裂，且维修必须整体更换，费用极高。',
      trap_explanation:
        '设计师或商家极力推荐岩板以获取更高利润，却隐瞒了其不耐冲击、维修困难的缺陷。对于普通家庭卫生间台面，石英石完全够用且耐用。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '4',
      category: '隐性成本',
      description: '衣帽间背板单价虚高——9mm板材比18mm柜体还贵？',
      severity: 'medium' as const,
      location: '全屋定制报价单-衣帽间（第七项）第2、5条',
      suggestion:
        '要求按市场合理价重新核价，或调整为同品牌18mm板材（单价315元/㎡）更加厚实且单价反而不高。',
      critique:
        '衣帽间1号柜和2号柜的背板采用9mm板材，单价220元/㎡，而18mm柜体（金丝橡木）单价才315元/㎡。背板用量少但单价竟然达到柜体的70%，明显定价过高。市场上9mm颗粒板背板成本通常在100-150元/㎡。',
      trap_explanation:
        '商家利用业主对"背板"不关注的特点，故意抬高背板单价来拉高整体报价，属典型的价格陷阱。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '5',
      category: '隐性成本',
      description: '整体报价折扣混乱——8折优惠后的"硬装转化客户"再8折，实际总价仍高达48800元',
      severity: 'medium' as const,
      location: '报价单底部总计栏',
      suggestion:
        '要求逐项核对所有单价和工程量，按展开面积重新计算，并明确折扣基数；建议对比其他定制品牌报价。',
      critique:
        '报价单显示：7项总和58452.55元，其余柜体五金44522.5元，合计10587.2元？但计算逻辑极混乱。最终给出"硬装转化客户8折优惠"后为47865.4元，然后又加了10587.2元得到48879.48元，再取整为48800元。这明显是故意制造复杂计算让业主难以核对，隐藏了多收费用。',
      trap_explanation:
        '装修公司常用的"打折诱导"套路：先报高价，再给折扣制造优惠假象，同时通过在单项报价中加水（如背板价、玻璃门价）转移利润。实际优惠有限。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '6',
      category: '卫生死角',
      description: '半包预算中卫生间防水与用户备注矛盾——墙地面不做二遍防水？',
      severity: 'critical' as const,
      location: '半包预算表-主卫生间（第6条）、次卫生间（第6条）、厨房（第5条）',
      suggestion:
        '立即与施工方确认：明确要求按国家标准做两遍防水（尤其是淋浴区），且必须做闭水试验。如果业主确实不想做（不推荐），则应在预算中删除对应款项并签字确认。',
      critique:
        '预算表显示主卫、次卫均做"墙地面做二遍防水处理"，单价42元/㎡且墙面整体到顶，但用户上传的备注文件明确写"墙地面不做二遍防水处理"。这属于严重的安全隐患——卫生间防水是隐蔽工程，一旦漏做将导致邻里纠纷和巨大返修成本。预算与备注不一致，可能施工方会按预算施工（多收防水费）或按备注减项（少做防水）。',
      trap_explanation:
        '预算与业主需求不一致，可能设计师或施工方故意多列防水项以增加预算，或业主事后改动未更新预算，需要明确确认。',
      regulation_ref: 'GB 50209-2010 建筑地面工程施工质量验收规范',
      image_refs: [],
      coordinates: [],
    },
    {
      id: '7',
      category: '安全与健康',
      description: '电线规格与备注不符——预算用多种规格，备注统一用2.5平方多芯线',
      severity: 'critical' as const,
      location: '半包预算表-水电（第3-5条） vs 用户备注',
      suggestion:
        '必须重新出具符合备注要求的电线预算：所有回路统一使用2.5平方多芯线（BVR），并确认空调、厨房是否需独立4平方回路；要求出具详细的回路设计方案。',
      critique:
        '预算表中分别列出了1.5平方（灯具线）、2.5平方（普通插座）、4平方（大功率电器）三种规格，总长度1340米。但用户备注明确"电线布线都是用的2.5平方的多芯线"。多芯线（BVR）与标准单芯线（BV）不同，且统一2.5平方可能导致大功率电器（如空调、烤箱）线径不足，有安全隐患。预算与实际要求严重不符。',
      trap_explanation:
        '要么是预算编制时未按业主需求调整，要么是施工方准备用低价单芯线替代。多芯线成本更高但施工便捷性较差，需确认是否明确要求。',
      regulation_ref: 'GB 50054-2011 低压配电设计规范',
      image_refs: [],
      coordinates: [],
    },
    {
      id: '8',
      category: '卫生死角',
      description: '卫生间/厨房顶角石膏线——纯装饰且易积灰',
      severity: 'medium' as const,
      location: '半包预算表-卫生间（第8条）、厨房（第7条）',
      suggestion:
        '卫生间厨房建议使用集成吊顶配套的PVC或不锈钢收边条，美观且易清洁，或者不做顶角线。',
      critique:
        '预算中卫生间和厨房均安装了"配套顶角线"（石膏线），卫生间湿区石膏线易受潮发霉，且顶角线是积灰死角，清洁困难。厨房油烟重，石膏线更易吸附油污变黄。这些区域的顶角线除了增加装饰费用，毫无实用价值。',
      trap_explanation:
        '装修公司为了提升总价和施工复杂度，推荐在非必要区域安装石膏线，但业主往往后期发现清洁麻烦且容易损坏。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '9',
      category: '隐性成本',
      description: '角阀数量与备注矛盾——备注定19个，预算却列了35个',
      severity: 'medium' as const,
      location: '半包预算表-水电（第7条） vs 用户备注',
      suggestion:
        '按实际需求重新核实角阀数量。两室一厅一般需要：厨房2个、卫生间4个、洗衣机1个、热水器2个，共约9-12个。建议按用户备注的19个（已偏多）为准结算。',
      critique:
        '预算列出的角阀数量高达35个，即便一套两室一厅的房子把所有用水点都算上，也不超过15-20个。35个角阀意味着平均每个用水点装了3-4个，明显虚报。',
      trap_explanation:
        '角阀等小五金是装修公司常用的"数量陷阱"——单价不起眼，但数量翻倍后总价可观。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '10',
      category: '隐性成本',
      description: '地漏数量超额——35个地漏比正常多出2-3倍',
      severity: 'medium' as const,
      location: '半包预算表-水电（第6条）',
      suggestion:
        '两室一厅通常只需：卫生间干区1个、湿区1个、阳台1个、厨房1个（可选），共3-4个。建议按实际需求核算。',
      critique:
        '预算中列出的地漏高达35个之多！即便每平米装一个也用不了35个地漏。这种明显的数据错误要么是复制粘贴时的笔误，要么是故意虚增数量。',
      trap_explanation:
        '极不合理的数量说明预算编制质量极差或存在恶意增项。业主几乎不可能注意到底部的小项数量。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
    {
      id: '11',
      category: '卫生死角',
      description: '客餐厅吊顶剖面复杂造型——积灰且压层高',
      severity: 'medium' as const,
      location: '客餐厅吊顶剖面图',
      suggestion:
        '建议简化吊顶造型：不做复杂叠级，改用平顶+嵌入式射灯，或直接做边吊。既省钱又减少积灰死角。',
      critique:
        '吊顶设计了多层叠级造型，这种设计容易积灰且清洁极为困难。每次大扫除都需要爬梯子用掸子清理。同时多层吊顶压缩了层高，对于普通住宅（层高2.8m左右）会让空间显得压抑。',
      trap_explanation:
        '复杂吊顶是装修公司提高利润的法宝——施工工艺复杂、人工费高、材料用量大，但对业主来说百害而无一利。',
      regulation_ref: null,
      image_refs: [],
      coordinates: [],
    },
  ],
  document_analyses: {
    'file-001': {
      id: 'doc-analysis-001',
      project_id: 'demo-project-001',
      project_file_id: 'file-001',
      status: 'completed' as const,
      doc_type: 'quotation',
      confidence: 0.92,
      summary:
        '该报价单存在多处典型陷阱：背板单价虚高（9mm板材220元/㎡）、玻璃门溢价严重（1260元/㎡）、层板灯增项过多（1450元）、岩板台面性价比极低（2176元）。整体报价在8折后仍高达48800元，建议重新议价。',
      total_estimated_risk: '约 8000-12000 元水分',
      risks_count: 5,
      risks: [
        {
          id: 'risk-quo-1',
          category: 'billing_trap' as const,
          title: '衣帽间背板单价虚高',
          original_text: '9mm背板 220元/㎡',
          critique:
            '9mm颗粒板背板市场价一般在100-150元/㎡，220元/㎡明显偏高。相比之下18mm柜体板才315元/㎡，背板价格竟然达到柜体的70%。',
          financial_consequence: '多付约500-800元',
          suggested_fix: '要求按市场价（不超过150元/㎡）重新核算，或要求免费升级为18mm同材质背板。',
        },
        {
          id: 'risk-quo-2',
          category: 'extra_item' as const,
          title: '铝框玻璃门全做不做选配',
          original_text: '3扇铝框玻璃门（浅金色极窄铝框+欧茶玻璃）单价1260元/㎡，合计5027元',
          critique:
            '衣帽间3扇门全部采用昂贵的铝框玻璃门，没有提供爱格板门板（520元/㎡）的标准选项。设计师或商家未告知业主有其他选择。',
          financial_consequence: '比普通爱格板门板多付约3500元',
          suggested_fix: '全部改用爱格板门板（520元/㎡），如需通透效果，仅中间一扇做玻璃门。',
        },
        {
          id: 'risk-quo-3',
          category: 'extra_item' as const,
          title: '全屋10根层板灯——严重过度配置',
          original_text: '45度层板灯 × 10根，单价145元/根，合计1450元',
          critique:
            '鞋柜、衣柜内部安装层板灯几乎没有实际用途。日常使用中，这些灯带几乎不会开启，反而增加电池更换（或接线）成本和故障率。',
          financial_consequence: '多付1450元',
          suggested_fix: '仅保留客厅展示区1-2根氛围灯，其余全部取消，省下约1000元。',
        },
        {
          id: 'risk-quo-4',
          category: 'billing_trap' as const,
          title: '岩板台面高价低质',
          original_text: '主卫台面岩板 1860元/m，1.17m合计2176元',
          critique:
            '岩板虽外观精致，但脆性大、易崩边、维修困难。对于卫生间台面，用石英石（1180元/m）完全够用且更耐用。',
          financial_consequence: '多付约800元',
          suggested_fix: '改用15mm石英石台面（同预算其他项目），节省约800元且更耐用。',
        },
        {
          id: 'risk-quo-5',
          category: 'contract_clause' as const,
          title: '折扣计算逻辑混乱',
          original_text:
            '7项总和58452.55元，其余柜体五金44522.5元 → 合计10587.2元 → 8折后47865.4元 → 再加10587.2元 → 取整48800元',
          critique:
            '折扣计算过程让人难以理解：为什么是先打折再加回一部分价格？这种模糊的算法极易隐藏多收费。',
          financial_consequence: '视计算方式差异可能在2000-5000元不等',
          suggested_fix: '要求逐项列出明细并按展开面积重新计算，明确折扣基数后再给最终总价。',
        },
      ],
      created_at: '2026-01-15T10:45:00Z',
      extra_item_prediction: {
        quoted_total: 48800,
        predicted_actual_total: 62000,
        confidence_range: [58000, 68000],
        risk_level: 'high',
        predicted_items: [
          {
            name: '水电增项（加插座/移位）',
            probability: '90%',
            estimated_amount: [3000, 5000],
            trigger_phase: '水电施工',
            reason: '备注要求全部用2.5平方多芯线，与预算规格不符，可能产生材料变更费用',
            prevention: '施工前确认所有回路设计方案并签字锁定价格',
          },
          {
            name: '瓷砖倒角/拼花加工费',
            probability: '75%',
            estimated_amount: [1500, 3000],
            trigger_phase: '泥工阶段',
            reason: '预算未明确倒角、海棠角等加工费用，施工中通常会以"工艺要求"为由加收',
            prevention: '在合同中明确所有加工费用包含在报价内',
          },
          {
            name: '吊顶造型变更/加固',
            probability: '65%',
            estimated_amount: [2000, 4000],
            trigger_phase: '木工阶段',
            reason: '图纸与现场可能出现偏差，或业主现场要求调整造型',
            prevention: '施工前确认所有吊顶图纸并注明变更费用由施工方承担',
          },
        ],
      },
    },
    'file-002': {
      id: 'doc-analysis-002',
      project_id: 'demo-project-001',
      project_file_id: 'file-002',
      status: 'completed' as const,
      doc_type: 'quotation',
      confidence: 0.88,
      summary:
        '半包预算存在多项与用户备注的矛盾：防水处理、电线规格、角阀数量等均与业主需求不符。预算中部分项目数量明显异常（地漏35个、角阀35个），存在虚报嫌疑。',
      total_estimated_risk: '约 5000-8000 元水分',
      risks_count: 4,
      risks: [
        {
          id: 'risk-budget-1',
          category: 'billing_trap' as const,
          title: '卫生间/厨房顶角线（石膏线）——受潮发霉风险',
          original_text: '卫生间、厨房配套顶角线安装',
          critique:
            '在卫生间和厨房等潮湿/油烟区域安装石膏顶角线，石膏线易吸湿发霉、吸附油烟变黄，且顶角线是卫生死角，清洁困难。',
          financial_consequence: '多付约800-1200元，后续更换成本更高',
          suggested_fix: '建议取消卫生间厨房石膏线，改用集成吊顶配套收边条，或不做顶角线。',
        },
        {
          id: 'risk-budget-2',
          category: 'billing_trap' as const,
          title: '地漏数量严重虚报——35个地漏',
          original_text: '地漏 35个',
          critique:
            '两室一厅正常只需要3-4个地漏（卫生间干区1、湿区1、阳台1、厨房可选1）。35个地漏意味着每平米一个，显然是数据错误或恶意虚报。',
          financial_consequence: '多付约1000-1500元',
          suggested_fix: '按实际需求核算，两室一厅建议不超过4个，多出部分从预算中删除。',
        },
        {
          id: 'risk-budget-3',
          category: 'billing_trap' as const,
          title: '角阀数量远超实际需求',
          original_text: '角阀 35个',
          critique:
            '用户备注明确注明了19个角阀（已偏多），预算却列出35个。两室一厅正常只需要10-15个角阀。',
          financial_consequence: '多付约500-800元',
          suggested_fix: '按用户备注的19个核算，35个明显不合理。',
        },
        {
          id: 'risk-budget-4',
          category: 'contract_clause' as const,
          title: '电线规格与用户备注严重不符',
          original_text: '1.5平方线300米、2.5平方线700米、4平方线340米',
          critique:
            '用户明确要求"所有电线统一使用2.5平方多芯线（BVR）"，但预算仍然按传统配置列出1.5/2.5/4平方三种规格三种长度。不仅规格不符，而且多芯线（BVR）与预算中的单芯线（BV）价格不同。',
          financial_consequence: '变更可能产生额外材料费约2000-3000元',
          suggested_fix: '按用户要求重新出水电方案：统一2.5平方多芯线，空调等大功率电器确认是否需要4平方。',
        },
      ],
      created_at: '2026-01-15T10:50:00Z',
    },
  },
  cross_document_checks: {
    check_mode: 'auto',
    document_pairs: ['全屋定制报价单.pdf', '半包预算表.pdf'],
    pair_type: 'BILL_vs_CONTRACT',
    discrepancies: [
      {
        type: 'scope_overlap',
        severity: 'medium' as const,
        description: '柜体报价与半包预算中的柜体项目可能存在重叠',
        source_a: '全屋定制报价单-全部7项',
        source_b: '半包预算表-柜体相关项',
        risk: '可能导致重复计费或遗漏，需确认哪些柜体包含在半包预算中',
        suggested_action: '提供明确的分项清单，区分全屋定制与半包预算各自涵盖的柜体范围',
      },
    ],
    summary:
      '两份文档覆盖的施工范围不同：全屋定制报价单针对特定柜体（橱柜、衣柜等），半包预算合同主要针对全房基础装修（水电、泥木、油漆等）。两者之间未发现直接的跨文档价格矛盾，但需注意施工范围的衔接和避免重复计费。',
  },
  created_at: '2026-01-15T11:00:00Z',
  completed_at: '2026-01-15T11:05:00Z',
}

export const DEMO_PROJECTS_LIST = [DEMO_PROJECT]