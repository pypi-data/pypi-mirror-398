# Changelog

## [5.12.261]
### Added
- (seba) `Hatch` 加入 `updated_at`

## [5.10.82]
### Fixed
- (seba) `Hatch` `mcp_config`設錯

## [5.10.81]
### Updated
- (seba) `Hatch` 加入 `mcp_config`

## [5.6.101]
### Updated
- (seba) `Hatch` 加入 `last_sync_gdoc_success`

## [5.6.62]
### Updated
- (seba) `Hatch` `last_sync_gdoc_time` 預設為空字串

## [5.6.61]
### Added
- (seba) `Hatch` 加入 `last_sync_gdoc_time`

## [5.6.54]
### Added
- (seba) 加入 `HatchWebhook`

## [5.6.53]
### Updated
- (seba) `Hatch` 的 `prompt_template`是 Optional

## [5.6.52]
### Updated
- (seba) `Hatch` 的 `google_doc_link`, `enable_google_doc_link`是 Optional

## [5.6.51]
### Added
- (seba) `Hatch` 加入 `google_doc_link`, `enable_google_doc_link`

## [5.5.201]
### Added
- (seba) 加入 `HatchSharing`

## [5.3.172] - 2025-03-17
### Updated
- (seba) 修改 hatch 的格式，加入 `agent_model_name` 欄位

## [5.3.171] - 2025-03-17
### Updated
- (seba) 修改 user_setting 的格式，加入 `api_key` 欄位

## [5.3.151] - 2025-03-15
### Updated
- (seba) 修改 hatch 的格式，加入 `enable_api` 欄位

## [5.3.141] - 2025-03-14
### Updated
- (seba) 整個專案調整，把 reflex 拿掉，把 hatch, upload_file, user_setting 的 model 加入

## [4.10.92] - 2024-10-09
### Updated
- (seba) 波特人設定，改成 AI Agent 設定

## [4.10.91] - 2024-10-09
### Updated
- (seba) 修改返回聊天的字樣
- (seba) 返回聊天的時候，會 reload 原本的視窗
- (seba) 前端會在 url 加上 /settings/ 的 path，並且放在 botrun_chat 的專案裡面執行
- (seba) 設定頁面的 prompte template 裡的字調大
- (seba) 設定頁面的 prompte template 的預設行數變多

## [4.10.51] - 2024-10-05
### Added
- (seba) 加入可以調整 system prompt 的流程

## [4.9.271] - 2024-09-27
### Added
- (seba) init project
