# 台新信用卡權益知識圖譜 — Neo4j Document Intelligence Model

把 `raw/` 底下的信用卡客服 KM 文件（共 9 份 PDF）匯入 Neo4j Aura **Document Intelligence**，由它依照這份 graph model 抽取實體與關係。

## 產出物

| 檔案 | 用途 |
|---|---|
| `output/graph_model.json` | **匯入用 model**：Neo4j 官方 graph-schema JSON（`graphSchemaRepresentation`），17 個 node label、28 個 relationship type、44 個 pattern，每個 label／property／pattern 都帶中文 `description` 給 LLM 抽取時參考，並為每個 label 的 key 建立 uniqueness constraint |
| `output/di_agent_prompt.md` | 同一份 model 的自然語言版本，可直接貼給 Document Intelligence 內建 agent |
| `output/model_diagram.md` | Model 關係圖（Mermaid，GitHub 會直接渲染） |
| `queries/check_graph.cypher` | 匯入後的品質檢查與客服問答查詢 |
| `ontology.yaml` | **唯一來源**；以上 `output/` 檔案都由它產生，請勿手改 `output/` |

## 匯入 Document Intelligence

1. Aura console → 你的 instance → **Document Intelligence** → **Graph model** → **Create graph model**，資料來源選 local files，上傳 `raw/*.pdf`（9 份，在 20 份上限內）。
2. 設定 model，擇一：
   - **A. 上傳 JSON**：model 編輯器若提供上傳 / import model（`.json`）的選項，上傳 `output/graph_model.json`。
   - **B. 交給 agent**：選擇不自動產生 model，把 `output/di_agent_prompt.md` 全文貼給內建 agent，請它依此建立 model。
   - **C. 對齊自動產生的 model**：讓 Document Intelligence 先自動產生，再把 `di_agent_prompt.md` 貼給 agent，要求「依此 model 調整：只保留這些 label 與 relationship、改用這些名稱與 key」。
3. 用 **Preview** 抽樣檢查：卡號前 8 碼是否為 8 位數字、民國年是否轉成西元、同一廠商是否只有一個節點。
4. **Run import**，完成後在 Query 頁逐段執行 `queries/check_graph.cypher`。

> **尚未驗證的部分**：我在建立此 model 時無法連上 neo4j.com 的 Document Intelligence 文件，所以沒辦法確認 model 編輯器是否接受上傳 JSON、或接受哪一種 JSON。`graph_model.json` 依 Neo4j 官方 graph-schema JSON 規格產生，並通過官方 JSON Schema（`@neo4j/graph-json-schema`）與解析器（`@neo4j/graph-schema-utils`）驗證。若上傳被拒，改用方式 B 或 C，兩者用的是同一份 model。

## Model 設計

完整圖見 [`output/model_diagram.md`](output/model_diagram.md)。核心結構：

```
CreditCard ─HAS_BIN→ CardBIN ─MAPPED_TO_PLAN→ RewardPlan ─HAS_REWARD_RULE→ RewardRule ─APPLIES_TO/EXCLUDES→ SpendingCategory / Merchant
     │                                            │
     ├─HAS_TERM→ BenefitTerm ─FOR_BENEFIT→ Benefit ─PROVIDED_BY→ Partner ─OPERATES→ ServiceLocation ─SERVES_AIRPORT→ Airport
     └─HAS_TIER→ CardTier ─HAS_TERM→ BenefitTerm   └─INCLUDES_BENEFIT→ Benefit
Procedure ─HANDLES→ Benefit / RewardPlan / CreditCard ； Procedure ─USES_SYSTEM→ InternalSystem ； FAQ ─ABOUT→ …
```

設計重點：

- **權益條款獨立成 `BenefitTerm` 節點**：同一個權益（例如機場停車）對不同卡別有不同門檻、次數、天數，旅平險對不同卡等級有不同保額。把這些放在節點上而不是關係屬性上，LLM 比較抽得到，查詢也能直接比較數值欄位（`spend_threshold`、`lookback_months`、`usage_limit_count`）。
- **卡別與卡等級分開**：保險、市區停車等權益是依卡等級（御璽卡、白金卡…）給的，`CardTier` 可以直接掛 `BenefitTerm`。
- **卡號前 8 碼是一級實體**：太陽／玫瑰卡的方案是依前 8 碼判斷（`CardBIN -MAPPED_TO_PLAN→ RewardPlan`），這是客服最常查的事。
- **排除項目用關係表示**：「不回饋」「不列入門檻」的消費類別以 `EXCLUDES` 連到 `SpendingCategory`，不另開 label。
- **客服作業程序（`Procedure`）**：個案辦法、出單方式、系統異常處理、話術都抽成節點，帶授權角色（`approver`）、次數限制（`limit`）、MTMF 註記格式（`memo_format`）。
- **不抽個資**：抽取規則明確要求不建立員工姓名、員編、Email、客戶資料的節點或屬性（文件中有權益 PM 的姓名與員編）。
- **不定義 `Document` / `Chunk`**：這些是 Document Intelligence 自動建立的 lexical layer，model 裡重複定義會衝突。

## 修改 model

```bash
# 1. 編輯 ontology.yaml（新增 label / property / relationship，或修改 description）
# 2. 重新產生 output/（會先檢查 ontology 一致性）
python3 kg_model/build_model.py
# 3. 用 Neo4j 官方規格驗證 graph_model.json
cd kg_model/validate && npm install && npm run validate
```

`ontology.yaml` 中 `{...}` 寫法的 property，若 description 含半形逗號 `,` 必須用雙引號包起來，否則 YAML 會把它切成多個欄位；`build_model.py` 會檢查並報錯。`python3 kg_model/build_model.py --check` 可在 CI 中確認 `output/` 與 `ontology.yaml` 同步。
