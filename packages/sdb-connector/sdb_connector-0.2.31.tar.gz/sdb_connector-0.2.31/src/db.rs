use serde::{Deserialize, Serialize};
use surrealdb::Surreal;
use surrealdb::opt::auth::Root;
use surrealdb::engine::remote::http::Client;
use surrealdb::engine::remote::http::Http;
use std::error::Error;
use chrono::{DateTime, Utc};

use crate::db;

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AmvStaticInfo {
    pub timestamp: DateTime<Utc>,
    pub ip_address: [u8; 4],
    pub number_of_channels: u8,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UdpTag40 {
    pub counter: u64,
    pub created: String,
    pub firmware_revision: String,
    pub firmware_version: String,
    pub ip_address: Vec<u8>,
    pub ip_address_user_auto: Vec<u8>,
    pub konfiguration: String,
    pub mac_address: String,
    pub number_of_channels: u8,
    pub port: u16,
    pub run_counter: u32,
    pub serial_number: String,
    pub subnet_mask: Vec<u8>,
    pub timestamp: String,
    pub udp_port_sensor: u16,
    pub udp_port_user_auto: u16,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct UdpTag49 {
    pub run_counter: u64,
    pub len_trigger: u16,
    pub channel: Vec<u8>,
    pub peak: Vec<u16>,
    pub peak_position: Vec<u16>,
    pub position_over: Vec<u16>,
    pub position_under: Vec<u16>,
    pub offset_after: Vec<u16>,
    pub offset_before: Vec<u16>,
    pub timestamp: String,
    pub counter: u64,
    pub created: String,
}


#[derive(Debug, Serialize, Deserialize)]
pub struct UdpTag41 {
    pub run_counter: u64,
    pub channel: Vec<u8>,
    pub integral: Vec<u64>,
    pub mass: Vec<u64>,
    pub offset: Vec<u16>,
    pub offset1: Vec<u16>,
    pub offset2: Vec<u16>,
    pub tolerance_bottom: Vec<u16>,
    pub tolerance_top: Vec<u16>,
    pub timestamp: String,
    pub status: Vec<Vec<String>>,
    pub counter: u64,
    pub created: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct RawData {
    pub run_counter: u64,
    pub channel: u8,
    pub data: Vec<i32>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct AnalogInput {
    pub port: u8,
    pub pin: u8,
    pub timestamp: DateTime<Utc>,
    pub value: u16,
    pub run_counter: u64,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct DigitalInput {
    pub port: u8,
    pub pin: u8,
    pub timestamp: DateTime<Utc>,
    pub value: bool,
    pub run_counter: u64,
}


// Function to connect to the database
pub async fn connect_to_db(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str
) -> Result<Surreal<Client>, Box<dyn Error>> {
    let db = Surreal::new::<Http>(format!("{}:{}", ip, port)).await?;
    db.signin(Root {
        username: &format!("{}", user),
        password: &format!("{}", pw),
    })
    .await?;
    db.use_ns(&format!("{}", namespace)).use_db(&format!("{}", db_name)).await?;
    Ok(db)
}

pub async fn query_ai_data(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>> {
    let result_query = format!(
        "SELECT port, pin, timestamp, value, run_counter FROM {} WHERE run_id = {} ORDER BY run_counter ASC",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

pub async fn query_di_data(
   db: &Surreal<Client>,
   table_name: &str,
   run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>> {
    let result_query = format!(
        "SELECT port, pin, timestamp, value, run_counter FROM {} WHERE run_id = {} ORDER BY run_counter ASC",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

pub async fn query_measurement_data(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>>{
    let result_query = format!(
        "SELECT run_counter,channel, integral, mass, offset, offset1, offset2, tolerance_bottom, tolerance_top, timestamp, status, counter, created  FROM {} WHERE run_id = {} ORDER BY run_counter ASC",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

// Function to query data and process it
pub async fn query_additonal_info_data(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>>{
    let result_query = format!(
        "SELECT run_counter, len_trigger, channel, peak, peak_position, position_over, position_under, offset_after, offset_before, timestamp, counter, created FROM {} WHERE run_id = {} ORDER BY run_counter ASC",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

pub async fn query_raw_data(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>>{
    let result_query = format!(
        "SELECT run_counter,channel, data, timestamp FROM {} WHERE run_id = {} ORDER BY run_counter ASC",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

pub async fn query_general_information(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str
) -> Result<surrealdb::Response, Box<dyn Error>>{
    let result_query = format!(
        "select counter,created,firmware_revision,firmware_version,ip_address,
        ip_address_user_auto,konfiguration,mac_address,number_of_channels,port,run_counter,
        run_id,serial_number,status_opt,status_system,status_trigger,subnet_mask,
        timestamp,udp_port_sensor, udp_port_user_auto FROM {} WHERE run_id = {}",
        table_name, run_id
    );
    let result = db.query(&result_query).await?;
    Ok(result)
}

pub async fn query_amv_static_info(
    db: &Surreal<Client>,
    table_name: &str,
    run_id: &str,
) -> Result<Vec<AmvStaticInfo>, Box<dyn Error>> {
    // 1. Versuch: Datensatz mit passender run_id
    let query_by_run = format!(
        "SELECT ip_address, number_of_channels, timestamp FROM {} WHERE run_id = {} LIMIT 1",
        table_name, run_id
    );
    let mut result = db.query(&query_by_run).await?;
    let mut records: Vec<AmvStaticInfo> = result.take(0)?;

    if !records.is_empty() {
        return Ok(records);
    }

    // 2. Fallback: Neuester Datensatz (z.B. wenn amv_static_info noch keine run_id kennt)
    let fallback_query = format!(
        "SELECT ip_address, number_of_channels, timestamp FROM {} ORDER BY timestamp DESC LIMIT 1",
        table_name
    );
    let mut result = db.query(&fallback_query).await?;
    let records: Vec<AmvStaticInfo> = result.take(0)?;
    Ok(records)
}
