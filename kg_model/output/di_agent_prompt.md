# 台新信用卡權益知識圖譜 — Graph Model 說明（v1.0.0）

請依照以下 graph model 從文件中抽取實體與關係。只建立下列 node label 與 relationship type，不要新增其他類型；Document / Chunk 等 lexical layer 由系統自動建立。

## 抽取規則

- 文件為台新銀行信用卡客服知識庫（KM），以繁體中文原文抽取實體名稱，不要翻譯成英文。
- 民國年日期一律轉成西元 ISO 格式：115/1/1 → 2026-01-01；114/12/15 → 2025-12-15。
- 卡號前 8 碼一律寫成 8 位數字、不含連字號：4147-6321 → 41476321。
- 金額只保留數字（新臺幣元）：NT$30,000 → 30000；回饋率只保留百分比數值：1.2% → 1.2。
- 同一實體在不同文件出現時使用同一個名稱（例如「台灣快綫」「台灣快線」「aeroride 台灣快綫」統一為「aeroride台灣快綫」；「中興嘟嘟房」「嘟嘟房」統一為「中興嘟嘟房」）。
- 卡別與卡等級分開：「國泰航空鈦金卡」是 CreditCard，「鈦金卡」是 CardTier；「太陽卡 御璽」拆成 CreditCard「太陽卡」+ CardTier「御璽卡」。
- 不要抽取個人資料：員工姓名、員編、Email、客戶姓名、客戶電話一律不建立節點也不寫入屬性（廠商客服專線可以）。
- 「內部訊息」段落也要抽取，但在相關節點的描述性屬性中保留「內部」字樣，以便日後區分對外/對內口徑。

## Node labels

### CreditCard（key: `name`）

信用卡卡別（產品），例如太陽卡、玫瑰卡、台新Richart卡、環球無限卡、卓富無限卡、國泰航空世界卡、Mercedes-Benz無限卡、@GoGo卡、FlyGo卡。不含卡等級字樣時寫卡系列名稱。

- `name` (string, 必填)：卡別正式名稱（繁中原文），例如「太陽卡」「台新Richart卡」「國泰航空鈦金卡」。
- `aliases` (string[], 選填)：別名、舊名或簡稱，例如「原太陽卡/玫瑰卡(切換刷)」「賓士無限卡」。
- `card_family` (string, 選填)：卡系列或聯名品牌，例如「太陽玫瑰系列」「Richart」「國泰航空聯名」「Mercedes-Benz聯名」「新光三越聯名」。
- `is_cobrand` (boolean, 選填)：是否為聯名卡。
- `annual_fee` (string, 選填)：正卡／附卡年費說明，例如「正卡每年NT$4,500、附卡每年NT$4,500」。
- `annual_fee_waiver` (string, 選填)：免年費條件與年費減免個案辦法摘要。
- `issuing_status` (string, 選填)：發卡狀態：發行中／停止進件／已整併至其他卡別。

### CardTier（key: `name`）

卡等級，例如無限卡、世界卡、御璽卡、鈦金卡、晶緻卡、白金卡、金卡、普卡、商務鈦金卡、商務御璽卡、企業卡。

- `name` (string, 必填)：卡等級名稱，統一以「卡」結尾，例如「御璽卡」「白金卡」。
- `tier_group` (string, 選填)：文件中的分組說法，例如「一般卡別：御璽/鈦金/晶緻卡」「白金卡級以下」。

### CardBIN（key: `bin`）

卡號前 8 碼（BIN），用來判斷卡片適用的方案或權益，例如太陽卡 41476321、玫瑰卡 41476366、Richart卡 51572173。

- `bin` (string, 必填)：8 位數字、不含連字號，例如「41476321」。
- `network` (string, 選填)：國際組織：Visa／MasterCard／JCB（4 開頭為 Visa、5 開頭為 MasterCard、35 開頭為 JCB）。
- `org_code` (string, 選填)：ORG 代碼，例如「001」。
- `type_code` (string, 選填)：TYPE 代碼，例如「775」。
- `e_ticket` (string, 選填)：電子票證功能，例如「悠遊卡」「一卡通」；無則留空。
- `note` (string, 選填)：特殊說明，例如「113/6/28 後強制轉為切換刷方案」「可由自由選個案改為指定套餐」。

### RewardPlan（key: `name`）

回饋／權益方案，包含方案大類（自由選、指定套餐、切換刷）、切換刷子方案（Pay著刷、天天刷、大筆刷、好饗刷、數趣刷、玩旅刷、假日刷）、自由選套餐選項（行動生活、百貨血拚、旅行享樂、量販超市、虛擬網購、簡單回饋、自由組合、簡單雙享）。

- `name` (string, 必填)：方案名稱（原文），例如「指定套餐」「天天刷」「行動生活」「簡單雙享」。
- `plan_level` (string, 選填)：方案層級：方案大類／子方案／套餐選項。
- `description` (string, 選填)：方案內容摘要，例如「加油/汽修+餐廳+電信費」。
- `switch_rule` (string, 選填)：切換或選擇方式與限制，例如「正卡人每日23:59前透過Richart Life APP切換，每日限一次，ID歸戶」。
- `change_policy` (string, 選填)：可否變更方案及個案變更規定，例如「114/10/1起不開放個案變更」。
- `valid_from` (date, 選填)：活動或方案適用起日（ISO 日期）。
- `valid_to` (date, 選填)：活動或方案適用迄日（ISO 日期）。

### RewardRule（key: `name`）

消費回饋規則：某方案或卡別在某消費範圍的回饋率、門檻與上限，例如「指定套餐指定類別滿3萬回饋1.2%」「Richart卡保費1.3%」「一般消費0.3%無上限」。

- `name` (string, 必填)：規則唯一名稱，格式「<方案或卡別>-<消費範圍>-<回饋率>%」，例如「指定套餐-指定類別滿3萬-1.2%」「天天刷-指定通路-3.3%」。
- `reward_rate` (float, 必填)：回饋率百分比數值，例如 1.2、3.8。
- `reward_type` (string, 選填)：回饋形式：台新Point(信用卡)／現金回饋／刷卡金。
- `spend_scope` (string, 選填)：消費範圍：指定消費／一般消費／保費／海外消費／不限類別。
- `min_spend` (integer, 選填)：適用級距下限（新臺幣元），例如滿 3 萬寫 30000、1~29,999 寫 1。
- `max_spend` (integer, 選填)：適用級距上限（新臺幣元），例如 29999；無上限留空。
- `reward_cap` (string, 選填)：回饋上限，例如「每期1,500點台新Point」「無上限」「永久信用額度加計NT$30萬為限」。
- `calculation` (string, 選填)：計算方式，例如「當期帳單正附卡合併、四捨五入」「逐筆計算、小數點無條件捨去、ID歸戶」。
- `eligibility` (string, 選填)：其他適用條件，例如「需完成台新帳戶自動扣繳（LEVEL 2）」「限臺灣地區新臺幣交易」。
- `valid_from` (date, 選填)：適用起日（ISO 日期）。
- `valid_to` (date, 選填)：適用迄日（ISO 日期）。

### Benefit（key: `name`）

權益或附加優惠項目（目錄層級），例如國際機場週邊停車、市區臨時停車、加油站水刀洗車、機場接送、國內機場貴賓室、24小時道路救援、旅遊不便險、旅遊平安險、海外旅遊全程保障保險、信用卡購物保障、消費簡訊、海外消費1%回饋、機車路邊停車。

- `name` (string, 必填)：權益名稱（統一名稱），例如「國際機場週邊停車」「市區臨時停車」「加油站水刀洗車」「機場接送」。
- `category` (string, 選填)：權益類型：停車／接送／洗車／保險／貴賓室／道路救援／通知服務／回饋。
- `description` (string, 選填)：權益內容摘要。
- `usage_method` (string, 選填)：使用方式，例如「持實體卡與出國證明過卡檢核」「至全鋒洗金寶官網驗證身分領取電子憑證」。
- `effective_rule` (string, 選填)：生效時點規則，例如「申請變更之近一個營業日次日15:00起生效」。
- `valid_from` (date, 選填)：權益期間起日（ISO 日期）。
- `valid_to` (date, 選填)：權益期間迄日（ISO 日期）。

### BenefitTerm（key: `name`）

某卡別、卡等級或方案享有某權益的具體條款：消費門檻、檢核期間、次數、天數、時數或保額，例如「國泰航空鈦金卡-國際機場週邊停車：前6個月刷當次機票/團費達3萬，每年2次、每次5天」。

- `name` (string, 必填)：條款唯一名稱，格式「<卡別/卡等級/方案>-<權益名稱>」，例如「環球無限卡-國際機場週邊停車」「白金卡-旅遊不便險」。
- `spend_threshold` (integer, 選填)：消費門檻金額（新臺幣元），例如 30000、12000；「任刷一筆」寫 1。
- `threshold_rule` (string, 選填)：門檻條件原文摘要，例如「使用前3個月內(含使用當月)刷卡支付當次機票/旅遊團費合計達NT$30,000」。
- `lookback_months` (integer, 選填)：消費檢核回推月數，例如 6、3。
- `usage_limit` (string, 選填)：次數上限原文，例如「每年2次」「無限次」「每期1次」「每卡每日1次」。
- `usage_limit_count` (integer, 選填)：次數上限數值；無限次留空。
- `quota` (string, 選填)：每次可享額度，例如「5天/次」「每日2小時、每期10小時」「班機延誤每一事故1萬」。
- `holder_scope` (string, 選填)：正附卡適用範圍，例如「限正卡人」「正附卡合併計算」「同一ID同時僅能使用一張」。
- `valid_from` (date, 選填)：條款適用起日（ISO 日期）。
- `valid_to` (date, 選填)：條款適用迄日（ISO 日期）。

### SpendingCategory（key: `name`）

消費類別或交易類型，包含回饋指定類別（加油/汽車保修、百貨公司、餐廳、電信費、超市）、權益門檻認列類別（航旅消費：機票/旅遊團費/指定訂房網站）、以及不回饋或不列入門檻的排除類別（學費、eTag自動儲值、保險費、預借現金、便利商店、全聯福利中心、各繳費平台交易）。

- `name` (string, 必填)：類別名稱（原文），例如「加油/汽車保修」「航旅消費」「eTag自動儲值」。
- `definition` (string, 選填)：類別定義或認列範圍，例如「全臺加油站、汽車維修、汽車百貨精品之消費及eTag自動儲值」。
- `mcc_codes` (string, 選填)：對應的 MCC 代碼條件，例如「3000~3299, 4511, 4582, 4722, 4723, 5962, 7991, 7011, 7922」。

### Merchant（key: `name`）

特約商店、指定通路或品牌，例如7-11、全家、全聯福利中心、新光三越、遠東SOGO、IKEA、蝦皮、Agoda、Booking.com、中華航空、Uber。

- `name` (string, 必填)：商店或通路名稱（原文）。
- `aliases` (string[], 選填)：別名，例如「酷澎」「Coupang」。
- `recognition_rule` (string, 選填)：認列方式，例如「以信用卡簽單商店名稱判斷，店中店不加碼」「限臺灣地區門市消費」。

### PaymentMethod（key: `name`）

支付工具或交易方式，例如實體卡、台新Pay、台新Pay+、LINE Pay、Apple Pay、Google錢包、Samsung Pay、街口支付、台灣Pay、悠遊卡自動加值。

- `name` (string, 必填)：支付工具名稱（原文）。
- `note` (string, 選填)：限制或注意事項，例如「超商綁定台新Pay單筆限額NT$3,000」「115/1/1起不適用假日刷加碼」。

### Partner（key: `name`）

權益合作廠商或保險公司，例如中興嘟嘟房、台灣聯通、24TPS永固便利、車麻吉(Autopass)、全勝出國停車場、富士捷、全鋒洗金寶、aeroride台灣快綫、新光產物保險。

- `name` (string, 必填)：廠商統一名稱。
- `service_type` (string, 選填)：服務類型：機場停車／市區停車／洗車／機場接送／保險／道路救援。
- `phone` (string, 選填)：對外客服專線，例如「(02)2775-9359」。
- `website` (string, 選填)：官方網站或預約網址。
- `service_hours` (string, 選填)：客服或營業時間。

### ServiceLocation（key: `name`）

權益使用場站或據點，例如機場外圍停車場（全勝出國停車場、日月亭平安場、富士捷大園出國停車場、中興嘟嘟房機場周邊停車場、大程停車場、大鵬停車場、嘟嘟房台中機場二站）、市區停車場、洗車場站。

- `name` (string, 必填)：場站名稱（原文）。
- `location_type` (string, 選填)：場站類型：機場外圍停車場／市區停車場／洗車場。
- `address` (string, 選填)：地址。
- `phone` (string, 選填)：場站電話。
- `opening_hours` (string, 選填)：營業時間。
- `member_price` (string, 選填)：台新卡友價或超出免費天數的收費，例如「每日200元」。
- `is_announced` (boolean, 選填)：是否為對外公告的配合場站（「不對外公告」「洽談中」為 false）。
- `service_notes` (string, 選填)：現場服務說明，例如「航站與停車場間免費接駁、不需留車輛鑰匙、可停休旅車」。

### Airport（key: `name`）

機場，例如桃園國際機場、松山國際機場、臺中清泉崗機場、高雄小港國際機場。

- `name` (string, 必填)：機場正式名稱，統一用「臺中清泉崗機場」「高雄小港國際機場」等全名。
- `iata_code` (string, 選填)：IATA 代碼（文件有提到才填），例如 TPE、TSA、RMQ、KHH。

### Region（key: `name`）

縣市或地區，用於場站所在地與機場接送免費指定區域，例如臺北市、新北市、桃園市、新竹縣市、臺中市、高雄市。

- `name` (string, 必填)：縣市名稱，「台」統一寫成「臺」，例如「臺北市」。

### Procedure（key: `name`）

客服作業程序：個案處理辦法、出單方式、系統異常處理、補點/補回饋、方案變更、客訴應對話術等，例如「機場停車-個案開放統一做法」「機場停車-離場過卡無法檢核且有進場紀錄」「自由選-回饋方式個案調整(點數改刷卡金)」。

- `name` (string, 必填)：程序唯一名稱，格式「<主題>-<情境>」。
- `procedure_type` (string, 選填)：程序類型：個案處理／出單／系統異常處理／補點補回饋／方案變更／話術。
- `trigger_condition` (string, 選填)：適用情境，例如「航旅消費未達檻」「廠商電話無法撥通」。
- `steps` (string, 選填)：處理步驟摘要（依序）。
- `approver` (string, 選填)：授權或裁示角色，例如「客服」「客服組長」「客服主管」「PM」「帳務」；不要寫人名。
- `limit` (string, 選填)：次數限制，例如「每人一生一次（含Never Say No）」「115/1/1~6/30間2次」。
- `memo_format` (string, 選填)：MTMF/MEMO 註記格式，例如「X年X月個案提供機場停車+原因」。
- `script` (string, 選填)：對客戶的說明話術摘要。

### InternalSystem（key: `name`）

銀行內部系統、工單類型或客戶自助管道，例如iCare、Cybercard、MTMF、PCS白金過卡系統、IPS工單、SFA、Richart Life APP、台新官網智能客服、行動銀行APP。

- `name` (string, 必填)：系統或管道名稱（原文）。
- `system_type` (string, 選填)：類型：內部系統／工單／客戶自助管道。
- `usage` (string, 選填)：用途，例如「查詢客戶目前方案（加油(新)/百貨(新)為指定套餐）」。

### FAQ（key: `question`）

文件中的常見問答（Q&A），一題一個節點。

- `question` (string, 必填)：問題原文（去掉「Q1：」等編號）。
- `answer` (string, 必填)：答案摘要，保留關鍵條件、金額與例外。

## Relationship types

- **HAS_TIER**：卡別或卡號前8碼所屬的卡等級。 模式：`(:CreditCard)-[:HAS_TIER]->(:CardTier)`、`(:CardBIN)-[:HAS_TIER]->(:CardTier)`
- **HAS_BIN**：卡別擁有的卡號前8碼。 模式：`(:CreditCard)-[:HAS_BIN]->(:CardBIN)`
- **MAPPED_TO_PLAN**：卡號前8碼預設對應的方案（例如 41476321 → 指定套餐、太陽卡 6 個卡號 113/6/28 起強制轉切換刷）。 模式：`(:CardBIN)-[:MAPPED_TO_PLAN]->(:RewardPlan)`
  - 關係屬性 `condition` (string)：對應條件或生效時間，例如「113/6/28後強制調整」。
- **OFFERS_PLAN**：卡別提供或可選擇的方案。 模式：`(:CreditCard)-[:OFFERS_PLAN]->(:RewardPlan)`
- **SUB_PLAN_OF**：子方案或套餐選項隸屬的上層方案，例如天天刷 → 切換刷、行動生活 → 自由選。 模式：`(:RewardPlan)-[:SUB_PLAN_OF]->(:RewardPlan)`
- **CAN_CHANGE_TO**：方案可變更（含個案變更）為另一方案。 模式：`(:RewardPlan)-[:CAN_CHANGE_TO]->(:RewardPlan)`
  - 關係屬性 `condition` (string)：變更條件，例如「僅限特定卡號前8碼、一次機會、由組長於Cybercard變更」「不開放」。
- **HAS_REWARD_RULE**：方案或卡別適用的回饋規則。 模式：`(:RewardPlan)-[:HAS_REWARD_RULE]->(:RewardRule)`、`(:CreditCard)-[:HAS_REWARD_RULE]->(:RewardRule)`
- **INCLUDES_BENEFIT**：方案內含或可勾選的附加優惠，例如自由選「行動生活」含市區雙品牌臨時停車。 模式：`(:RewardPlan)-[:INCLUDES_BENEFIT]->(:Benefit)`
  - 關係屬性 `condition` (string)：取得條件，例如「自由組合6選4」「需勾選且生效」。
- **HAS_BENEFIT**：卡別享有的權益。 模式：`(:CreditCard)-[:HAS_BENEFIT]->(:Benefit)`
  - 關係屬性 `condition` (string)：取得條件，例如「限指定套餐方案」「自由選需勾選國際機場週邊停車」。
- **HAS_TERM**：卡別、卡等級或方案擁有的權益條款。 模式：`(:CreditCard)-[:HAS_TERM]->(:BenefitTerm)`、`(:CardTier)-[:HAS_TERM]->(:BenefitTerm)`、`(:RewardPlan)-[:HAS_TERM]->(:BenefitTerm)`
- **FOR_BENEFIT**：權益條款所屬的權益項目。 模式：`(:BenefitTerm)-[:FOR_BENEFIT]->(:Benefit)`
- **APPLIES_TO**：回饋規則適用的消費類別或指定通路。 模式：`(:RewardRule)-[:APPLIES_TO]->(:SpendingCategory)`、`(:RewardRule)-[:APPLIES_TO]->(:Merchant)`
- **REQUIRES_PAYMENT**：回饋規則要求的支付工具（例如 Pay著刷限台新Pay綁定）。 模式：`(:RewardRule)-[:REQUIRES_PAYMENT]->(:PaymentMethod)`
- **COUNTS_SPENDING**：權益條款門檻認列的消費類別（例如機場停車門檻認列航旅消費）。 模式：`(:BenefitTerm)-[:COUNTS_SPENDING]->(:SpendingCategory)`
- **EXCLUDES**：回饋規則或權益門檻排除（不回饋／不列入計算）的消費類別、通路或支付工具。 模式：`(:RewardRule)-[:EXCLUDES]->(:SpendingCategory)`、`(:RewardRule)-[:EXCLUDES]->(:Merchant)`、`(:RewardRule)-[:EXCLUDES]->(:PaymentMethod)`、`(:BenefitTerm)-[:EXCLUDES]->(:SpendingCategory)`、`(:BenefitTerm)-[:EXCLUDES]->(:PaymentMethod)`
- **IN_CATEGORY**：商店或通路所屬的消費類別。 模式：`(:Merchant)-[:IN_CATEGORY]->(:SpendingCategory)`
- **PROVIDED_BY**：權益由哪個合作廠商提供。 模式：`(:Benefit)-[:PROVIDED_BY]->(:Partner)`
- **OPERATES**：廠商經營的場站。 模式：`(:Partner)-[:OPERATES]->(:ServiceLocation)`
- **AVAILABLE_AT**：權益可使用的場站。 模式：`(:Benefit)-[:AVAILABLE_AT]->(:ServiceLocation)`、`(:BenefitTerm)-[:AVAILABLE_AT]->(:ServiceLocation)`
- **SERVES_AIRPORT**：場站服務的機場（機場外圍停車場 → 機場）。 模式：`(:ServiceLocation)-[:SERVES_AIRPORT]->(:Airport)`
- **LOCATED_IN**：場站或機場所在縣市。 模式：`(:ServiceLocation)-[:LOCATED_IN]->(:Region)`、`(:Airport)-[:LOCATED_IN]->(:Region)`
- **TRANSFER_AREA**：機場接送免費指定區域（機場 → 可免費接送的縣市）。 模式：`(:Airport)-[:TRANSFER_AREA]->(:Region)`
- **MERGED_INTO**：舊卡別整併為新卡別，例如FlyGo卡、@GoGo卡、玫瑰Giving卡、太陽卡/玫瑰卡(切換刷)整併為台新Richart卡。 模式：`(:CreditCard)-[:MERGED_INTO]->(:CreditCard)`
- **HANDLES**：作業程序處理的權益、方案或卡別。 模式：`(:Procedure)-[:HANDLES]->(:Benefit)`、`(:Procedure)-[:HANDLES]->(:RewardPlan)`、`(:Procedure)-[:HANDLES]->(:CreditCard)`
- **USES_SYSTEM**：作業程序或方案切換使用的系統或管道（例如在Cybercard扣點、在MTMF註記、在PCS變更機場停車資料、在Richart Life APP切換方案）。 模式：`(:Procedure)-[:USES_SYSTEM]->(:InternalSystem)`、`(:RewardPlan)-[:USES_SYSTEM]->(:InternalSystem)`
- **CONTACTS_PARTNER**：作業程序需聯繫的廠商（例如個案需由客服致電停車場手抄、寄信台灣快綫代為預約）。 模式：`(:Procedure)-[:CONTACTS_PARTNER]->(:Partner)`
- **ABOUT**：常見問答涉及的權益、方案或卡別。 模式：`(:FAQ)-[:ABOUT]->(:Benefit)`、`(:FAQ)-[:ABOUT]->(:RewardPlan)`、`(:FAQ)-[:ABOUT]->(:CreditCard)`
- **REFERS_TO**：常見問答引用的作業程序。 模式：`(:FAQ)-[:REFERS_TO]->(:Procedure)`
