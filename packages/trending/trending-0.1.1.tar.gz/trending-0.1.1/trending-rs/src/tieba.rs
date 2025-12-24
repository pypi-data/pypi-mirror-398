use reqwest::Client as AsyncClient;
#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blocking")]
use crate::common::block_http_get;
use crate::{
  common::{EmptyType, PlatformType, TrendingRes, TrendingsRes, http_get},
  errors::Result,
};

pub const TRENDING_ENDPOINT: &'static str = "https://tieba.baidu.com/hottopic/browse/topicList";

pub async fn trending(client: &AsyncClient) -> Result<TrendingsRes> {
  http_get::<EmptyType, EmptyType, TiebaRes>(client, TRENDING_ENDPOINT, None, None, None)
    .await
    .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn blocking_trending(client: &BlockClient) -> Result<TrendingsRes> {
  block_http_get::<EmptyType, EmptyType, TiebaRes>(client, TRENDING_ENDPOINT, None, None, None)
    .map(|r| r.into())
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TiebaRes {
  #[serde(rename = "data")]
  data: TiebaData,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TiebaData {
  #[serde(rename = "bang_topic")]
  bang_topic: TiebaTopic,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TiebaTopic {
  #[serde(rename = "topic_list")]
  topic_list: Vec<TiebaItem>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct TiebaItem {
  #[serde(rename = "topic_name")]
  title: String,

  #[serde(rename = "topic_url")]
  url: String,

  #[serde(rename = "discuss_num")]
  trend: u64,
}

impl From<TiebaItem> for TrendingRes {
  fn from(value: TiebaItem) -> Self {
    Self {
      title: value.title,
      url: value.url,
      trend: Some(value.trend.to_string()),
    }
  }
}

impl From<TiebaRes> for TrendingsRes {
  fn from(value: TiebaRes) -> Self {
    Self {
      platform: PlatformType::Tencent,
      result: value
        .data
        .bang_topic
        .topic_list
        .into_iter()
        .map(|r| r.into())
        .collect(),
    }
  }
}
