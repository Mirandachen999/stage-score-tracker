# stage-score-tracker

學習冒險 — 關卡成績紀錄網站

參考語言學習 App 的深色闖關地圖，製作可在手機/電腦使用的學習成績記錄網站。

啟動網站（推薦：會自動寫入 TXT）

需要 Python 3（不需額外安裝套件）。在本資料夾開啟終端機：

python3 server.py

Windows 也可使用 python server.py。瀏覽器開啟 http://localhost:8000 。

每次儲存關卡會自動更新 data/records.txt，檔案內容是 JSON 格式，可用記事本、VS Code 開啟。

不啟動伺服器

直接用瀏覽器開啟 index.html 仍能操作，資料會存在該瀏覽器的 localStorage，不會寫入伺服器的 TXT。可在「設定 / TXT」匯出 records.txt，或匯入備份。

如果放在 GitHub Pages 等靜態網站，不能直接更新主機端的 TXT；需要有可寫入的後端（如附帶的 server.py）並部署在支援 Python 服務的主機。

功能

• 每階段 5 關，按「＋ 新階段」可持續新增，不限制為 30 階段（實際數量受裝置資源限制）。
• 每關可選擇 國文（粉紅）、數學（藍）、英文（紫）、自然（綠）、社會（橘），輸入 0–100 分數、備註；可修改和刪除。舊紀錄仍可讀取。
• 成績總分、已完成關卡數、平均分數、完成進度。
• 所有紀錄儲存在 data/records.txt，支援匯入/匯出。
• 無第三方依賴；手機與桌面瀏覽器可使用。

JSON 範例

{
  "version": 1,
  "sectionCount": 8,
  "records": {
    "8-1": {
      "subject": "英文",
      "score": 95,
      "notes": "單字測驗 95 分",
      "updatedAt": "2026-11-14T01:40:00.000Z"
    }
  }
}