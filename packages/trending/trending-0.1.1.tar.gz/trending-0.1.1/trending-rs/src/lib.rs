//! ### Trending
//!
//! Trending is a library for retrieving trending information from media platforms. It currently supports the following platforms:
//!
//! | platform      | trending | search | site                        |
//! | :-----------: | :------: | :----: | :-------------------------- |
//! | hupu          | ✓        | -      | <https://m.hupu.com>        |
//! | tencent       | ✓        | ✓      | <https://news.qq.com>       |
//! | netease       | ✓        | ✓      | <https://m.163.com>         |
//! | tieba         | ✓        | -      | <https://www.tieba.com>     |
//! | toutiao       | ✓        | -      | <https://www.toutiao.com>   |
//! | weibo         | ✓        | -      | <https://weibo.com>         |
//! | zhihu         | ✓        | -      | <https://www.zhihu.com>     |
//!
//! #### 1. Create AsyncClient
//! 
//! ```rust
//! use std::time::Duration;
//! use trending::{client::AsyncClient, errors::Result};
//! 
//! // new with default options
//! let client = AsyncClient::new();
//! 
//! // or new with custom options
//! let options = ClientOptions::new().with_timeout(Duration::from_secs(5));
//! let client = AsyncClient::new_with_options(options);
//! ```
//! 
//! #### 2. Trending Query
//! 
//! ```rust
//! // receive 29 trendings from zhihu
//! let res = client.trending_zhihu().await?;
//! println!("receive {} trendings from {}", res.result.len(), res.platform);
//! 
//! // 0 -> 货车司机往黄山拉玻璃，因两根松木框架被罚五千元，为何黄山对松木管控这么严格？
//! // ...
//! for (index, trending) in res.result.iter().enumerate() {
//!   println!("{:2} -> {}", index, trending.title);
//! }
//! ```
//! 
//! #### 2. Search Query
//! 
//! ```rust
//! let req = SearchReq::new("ELON");
//! 
//! let res = client.search_tecent(&req).await?;
//! // receive 20 trendings from tencent
//! println!("receive {} searches from {}", res.result.len(), res.platform);
//! 
//! // 0 -> 1万亿美元年薪，Elon Musk创纪录
//! // ...
//! for (index, search) in res.result.iter().enumerate() {
//!   println!("{:2} -> {}", index, search.title);
//! }
//! ```


pub mod client;
pub mod common;
pub mod errors;
mod hupu;
mod netease;
mod tencent;
mod tieba;
mod toutiao;
mod weibo;
mod zhihu;
