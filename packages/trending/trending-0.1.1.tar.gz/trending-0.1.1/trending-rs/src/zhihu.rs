use reqwest::Client as AsyncClient;
#[cfg(feature = "blocking")]
use reqwest::blocking::Client as BlockClient;
use serde::{Deserialize, Serialize};

#[cfg(feature = "blocking")]
use crate::common::block_http_get;
use crate::{
  common::{EmptyType, PlatformType, TrendingRes, TrendingsRes, http_get, not_empty_str},
  errors::Result,
};

pub const TRENDING_ENDPOINT: &'static str = "https://api.zhihu.com/topstory/hot-lists/total";

pub async fn trending(client: &AsyncClient) -> Result<TrendingsRes> {
  http_get::<EmptyType, EmptyType, ZhihuRes>(client, TRENDING_ENDPOINT, None, None, None)
    .await
    .map(|r| r.into())
}

#[cfg(feature = "blocking")]
pub fn block_trending(client: &BlockClient) -> Result<TrendingsRes> {
  block_http_get::<EmptyType, EmptyType, ZhihuRes>(client, TRENDING_ENDPOINT, None, None, None)
    .map(|r| r.into())
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct ZhihuRes {
  #[serde(rename = "data", skip_serializing_if = "Vec::is_empty", default)]
  data: Vec<ZhihuData>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct ZhihuData {
  #[serde(rename = "target")]
  target: ZhihuTarget,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
struct ZhihuTarget {
  #[serde(rename = "id")]
  id: u64,

  #[serde(rename = "type")]
  kind: String,

  #[serde(rename = "title")]
  title: String,

  #[serde(rename = "detail_text", skip_serializing_if = "Option::is_none")]
  detail_text: Option<String>,
  // #[serde(rename = "url")]
  // url: String,
}

impl From<ZhihuData> for TrendingRes {
  fn from(value: ZhihuData) -> Self {
    Self {
      title: value.target.title,
      url: format!(
        "https://www.zhihu.com/{}/{}",
        value.target.kind, value.target.id
      ),
      trend: not_empty_str(value.target.detail_text),
    }
  }
}

impl From<ZhihuRes> for TrendingsRes {
  fn from(value: ZhihuRes) -> Self {
    Self {
      platform: PlatformType::Zhihu,
      result: value.data.into_iter().map(ZhihuData::into).collect(),
    }
  }
}
