use std::error::Error;
use chrono::Duration;
use surrealdb::Response;

use crate::export;
use crate::db;

/// Steuert, ob nur Daten zurückgegeben, nur exportiert oder beides gemacht werden soll.
///
/// Mapping von `select_type`:
/// * `0` => `DataOnly`   – nur Daten nach Python zurückgeben, **kein** Excel-Export
/// * `1` => `ExportOnly` – nur Excel-Export, Rückgabe ist ein leeres `Vec`
/// * `2` => `Both`       – Excel-Export **und** Daten zurückgeben
#[derive(Copy, Clone, Debug, Eq, PartialEq)]
pub enum SelectMode {
    DataOnly,
    ExportOnly,
    Both,
}

impl SelectMode {
    pub fn from_u8(value: u8) -> Self {
        match value {
            1 => SelectMode::ExportOnly,
            2 => SelectMode::Both,
            _ => SelectMode::DataOnly,
        }
    }

    #[inline]
    pub fn needs_export(self) -> bool {
        matches!(self, SelectMode::ExportOnly | SelectMode::Both)
    }

    #[inline]
    pub fn needs_data(self) -> bool {
        matches!(self, SelectMode::DataOnly | SelectMode::Both)
    }
}

// -------------------- AI / DI ------------------------

pub async fn process_ai_data(
    result: Response,
    name: &str,
    select_type: u8,
) -> Result<Vec<(u8, u8, String, u16, u64)>, Box<dyn Error>> {
    let mut data = result;
    let data: Vec<db::AnalogInput> = match data.take(0) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error processing AI data: {:?}", e);
            return Err(Box::new(e));
        }
    };

    // Aktuell kein Excel-Export für AI – `select_type` wird hier nur für zukünftige Erweiterungen durchgereicht.
    let _ = name;
    let _ = select_type;

    let exploded_data: Vec<(u8, u8, String, u16, u64)> = data
        .into_iter()
        .map(|tag| {
            (
                tag.port,
                tag.pin,
                tag.timestamp.to_string(),
                tag.value,
                tag.run_counter,
            )
        })
        .collect();
    Ok(exploded_data)
}

pub async fn process_di_data(
    result: Response,
    path_name: &str,
    select_type: u8,
) -> Result<Vec<(u8, u8, String, bool, u64)>, Box<dyn Error>> {
    let mut data = result;
    let data: Vec<db::DigitalInput> = match data.take(0) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error processing DI data: {:?}", e);
            return Err(Box::new(e));
        }
    };

    // Aktuell kein Excel-Export für DI – `select_type` wird hier nur für zukünftige Erweiterungen durchgereicht.
    let _ = path_name;
    let _ = select_type;

    let exploded_data: Vec<(u8, u8, String, bool, u64)> = data
        .into_iter()
        .map(|tag| {
            (
                tag.port,
                tag.pin,
                tag.timestamp.to_string(),
                tag.value,
                tag.run_counter,
            )
        })
        .collect();
    Ok(exploded_data)
}

// -------------------- Additional Info ------------------------

pub async fn process_additonal_info_data(
    result: Response,
    ip_address: &str,
    name: &str,
    select_type: u8,
    number_of_channels: u8,
) -> Result<Vec<(u64, u16, u8, u16, u16, u16, u16, u16, u16, String)>, Box<dyn Error>> {
    let mut data_resp = result;
    let data: Vec<db::UdpTag49> = match data_resp.take(0) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting additional info data: {:?}", e);
            return Err(Box::new(e));
        }
    };

    let mode = SelectMode::from_u8(select_type);

    // Excel-Export nur, wenn explizit gewünscht
    if mode.needs_export() {
        export::store_additional_info_data_as_xlsx(&data, name, ip_address, number_of_channels)?;
    }

    // Nur Export gewünscht -> direkt zurück
    if !mode.needs_data() {
        return Ok(Vec::new());
    }

    let exploded_data: Vec<(u64, u16, u8, u16, u16, u16, u16, u16, u16, String)> = data
        .into_iter()
        .flat_map(|tag| {
            tag.channel
                .into_iter()
                .zip(tag.peak.into_iter())
                .zip(tag.peak_position.into_iter())
                .zip(tag.position_over.into_iter())
                .zip(tag.position_under.into_iter())
                .zip(tag.offset_after.into_iter())
                .zip(tag.offset_before.into_iter())
                .map(
                    move |((((((channel_value, peak_value), peak_position), position_over), position_under), offset_after), offset_before)| {
                        (
                            tag.run_counter,
                            tag.len_trigger,
                            channel_value,
                            peak_value,
                            peak_position,
                            position_over,
                            position_under,
                            offset_after,
                            offset_before,
                            tag.timestamp.clone(),
                        )
                    },
                )
        })
        .collect();
    Ok(exploded_data)
}

// -------------------- Measurement ------------------------

pub async fn process_measurement_data(
    result: Response,
    ip_address: &str,
    name: &str,
    select_type: u8,
    number_of_channels: u8,
) -> Result<Vec<(u64, u8, u64, u64, u16, u16, u16, u16, u16, String, Vec<String>)>, Box<dyn Error>> {
    let mut data_resp = result;
    let data: Vec<db::UdpTag41> = match data_resp.take(0) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting measurement data: {:?}", e);
            return Err(Box::new(e));
        }
    };

    let mode = SelectMode::from_u8(select_type);

    // Excel-Export nur, wenn explizit gewünscht
    if mode.needs_export() {
        export::store_measurement_data_as_xlsx(&data, name, ip_address, number_of_channels)?;
    }

    // Nur Export gewünscht -> direkt zurück
    if !mode.needs_data() {
        return Ok(Vec::new());
    }

    let exploded_data: Vec<(
        u64,
        u8,
        u64,
        u64,
        u16,
        u16,
        u16,
        u16,
        u16,
        String,
        Vec<String>,
    )> = data
        .into_iter()
        .flat_map(|tag| {
            tag.channel
                .into_iter()
                .zip(tag.integral.into_iter())
                .zip(tag.mass.into_iter())
                .zip(tag.offset.into_iter())
                .zip(tag.offset1.into_iter())
                .zip(tag.offset2.into_iter())
                .zip(tag.tolerance_bottom.into_iter())
                .zip(tag.tolerance_top.into_iter())
                .zip(tag.status.clone().into_iter())
                .map(
                    move |((((((((channel_value, integral), mass), offset), offset1), offset2), tolerance_bottom), tolerance_top), status)| {
                        (
                            tag.run_counter,
                            channel_value,
                            integral,
                            mass,
                            offset,
                            offset1,
                            offset2,
                            tolerance_bottom,
                            tolerance_top,
                            tag.timestamp.clone(),
                            status,
                        )
                    },
                )
        })
        .collect();
    Ok(exploded_data)
}

// -------------------- Raw data ------------------------

pub async fn process_raw_data(
    result: Response,
) -> Result<Vec<(u64, u8, i32, String, u32)>, Box<dyn Error>> {
    let mut ddata = result;
    let data: Vec<db::RawData> = match ddata.take(0) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting raw data: {:?}", e);
            return Err(Box::new(e));
        }
    };

    // Pre-allocate to reduce reallocations
    let total_samples: usize = data.iter().map(|tag| tag.data.len()).sum();
    let mut exploded_data = Vec::with_capacity(total_samples);

    for tag in data {
        let channel_value = tag.channel;
        let run_counter = tag.run_counter;
        let timestamp = tag.timestamp;

        for (i, data_value) in tag.data.into_iter().enumerate() {
            let duration: u32 = (i as u32) * 250;
            let new_timestamp =
                timestamp + Duration::microseconds((i as i64) * 250);
            exploded_data.push((
                run_counter,
                channel_value,
                data_value,
                new_timestamp.to_string(),
                duration,
            ));
        }
    }

    Ok(exploded_data)
}
