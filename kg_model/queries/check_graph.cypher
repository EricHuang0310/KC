// 匯入後的檢查查詢：在 Aura Query 逐段執行，確認 Document Intelligence 抽取結果符合 model。
// 1~3 是品質檢查（結果越少越好），4~9 是客服常見問題，能回答代表圖譜可用。

// 1. 各 label 節點數（有 label 為 0 代表該類實體沒抽到，回頭補強 description）
CALL db.labels() YIELD label
CALL (label) { MATCH (n) WHERE label IN labels(n) RETURN count(n) AS cnt }
RETURN label, cnt ORDER BY cnt DESC;

// 2. 疑似重複實體：名稱去空白、台/臺 統一後相同但仍是不同節點
MATCH (n)
WHERE n.name IS NOT NULL AND NOT n:Document AND NOT n:Chunk
WITH labels(n)[0] AS label, replace(replace(n.name, ' ', ''), '台', '臺') AS norm, collect(n.name) AS names
WHERE size(names) > 1
RETURN label, norm, names ORDER BY label;

// 3. 卡號前 8 碼格式錯誤（應為 8 位數字、無連字號）
MATCH (b:CardBIN) WHERE NOT b.bin =~ '\\d{8}'
RETURN b.bin;

// 4. 哪些卡號前 8 碼屬於「指定套餐」？
MATCH (c:CreditCard)-[:HAS_BIN]->(b:CardBIN)-[:MAPPED_TO_PLAN]->(p:RewardPlan {name: '指定套餐'})
RETURN c.name AS card, collect(b.bin) AS bins;

// 5. 各卡別的機場停車條款（門檻、次數、天數）
MATCH (owner)-[:HAS_TERM]->(t:BenefitTerm)-[:FOR_BENEFIT]->(:Benefit {name: '國際機場週邊停車'})
RETURN owner.name AS card_or_tier, t.threshold_rule, t.usage_limit, t.quota
ORDER BY t.usage_limit_count DESC;

// 6. 天天刷的回饋率與指定通路
MATCH (:RewardPlan {name: '天天刷'})-[:HAS_REWARD_RULE]->(r:RewardRule)
OPTIONAL MATCH (r)-[:APPLIES_TO]->(m:Merchant)
RETURN r.name, r.reward_rate, collect(m.name) AS merchants;

// 7. 某消費類別在哪些回饋規則被排除（例：便利商店）
MATCH (r:RewardRule)-[:EXCLUDES]->(s:SpendingCategory)
WHERE s.name CONTAINS '超商' OR s.name CONTAINS '便利商店'
RETURN s.name, collect(r.name) AS excluded_by;

// 8. 機場停車的個案處理程序：授權角色、次數限制、使用系統
MATCH (p:Procedure)-[:HANDLES]->(:Benefit {name: '國際機場週邊停車'})
OPTIONAL MATCH (p)-[:USES_SYSTEM]->(s:InternalSystem)
RETURN p.name, p.approver, p.limit, collect(s.name) AS systems;

// 9. 桃園機場外圍停車場與廠商、電話
MATCH (loc:ServiceLocation)-[:SERVES_AIRPORT]->(:Airport {name: '桃園國際機場'})
OPTIONAL MATCH (partner:Partner)-[:OPERATES]->(loc)
RETURN loc.name, partner.name, loc.phone, loc.is_announced;
