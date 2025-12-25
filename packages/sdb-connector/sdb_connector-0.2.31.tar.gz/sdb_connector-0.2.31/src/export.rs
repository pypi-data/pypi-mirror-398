// ignore snake case
#![allow(non_snake_case)]

use std::error::Error;
use xlsxwriter::*;

use crate::db;

/// Map Status-Codes aus UdpTag41 in sprechende deutsche Texte.
fn status_code_to_message(code: &str) -> &str {
    match code {
        "00" => "OK: Messwert im Toleranzbereich;",
        "01" => "OK: Der Massewert überschreitet den Toleranzbereich;",
        "02" => "OK: Der Massewert unterschreitet den Toleranzbereich;",
        "03" => "FEHLER: Offsetabgleich Anschlag Stellgröße oben;",
        "04" => "FEHLER: Offsetabgleich Anschlag Stellgröße unten;",
        "05" => "FEHLER: Offsetabgleich war noch nicht fertig, als die Flanke des Offsettriggers kam;",
        "06" => "FEHLER: Seit dem letzten Systemstart ist keine Messung vorhanden;",
        "07" => "FEHLER: Der Offset befindet sich außerhalb des Messbereichs;",
        "08" => "FEHLER: Der Messtrigger ist zu lang;",
        "09" => "FEHLER: Der Messtrigger ist zu kurz;",
        "10" => "FEHLER: Schräge Nulllinie: Schwellwert2 wurde nicht unterschritten;",
        "11" => "FEHLER: Schräge Nulllinie: Zeit t1 liegt vor der steigenden Flanke des Messtriggers;",
        "12" => "FEHLER: Schräge Nulllinie: Zeit t2 liegt nach der fallenden Flanke des Messtriggers;;",
        "13" => "FEHLER: Nulllinien Mittelung;",
        "14" => "FEHLER: Nulllinien Berechnung;",
        "15" => "FEHLER: maximal zulässige Anzahl von Umkehrpunkten wurde überschritten;",
        "16" => "FEHLER: maximal zulässige Amplitude des Rauschens wurde überschritten;",
        "17" => "FEHLER: Ein unzulässig hoher negativer Peak war vorhanden;",
        "0A" => "FEHLER: Anschlag des Messsignals;",
        "0B" => "FEHLER: Ein Variablenüberlauf bei der Masseberechnung ist aufgetreten;",
        "0C" => "FEHLER: Überwachung des Messfensters - positiv;",
        "0D" => "FEHLER: Überwachung des Messfensters - negativ;",
        "0E" => "FEHLER: Bei dem Offsetabgleich ist ein Timeout aufgetreten;",
        "0F" => "FEHLER: Schräge Nulllinie: Schwellwert1 wurde nicht überschritten;",
        _ => code,
    }
}

/// Wandelt einen Status-Vektor (z.B. `Vec<String>`) in einen zusammenhängenden Text.
pub fn error_matching(status_codes: &[String]) -> String {
    let mut out = String::new();
    for (idx, code) in status_codes.iter().enumerate() {
        if idx > 0 {
            out.push(',');
        }
        out.push_str(status_code_to_message(code));
    }
    out
}

/// Gemeinsame Export-Funktion für alle Kanalzahlen (1..=12) für Additional-Info (UdpTag49).
pub fn store_additional_info_data_as_xlsx(
    data: &[db::UdpTag49],
    name: &str,
    ip: &str,
    number_of_channels: u8,
) -> Result<(), Box<dyn Error>> {
    if number_of_channels == 0 {
        return Ok(());
    }

    let workbook = Workbook::new(name)?;
    let mut worksheet = workbook.add_worksheet(None)?;

    // Kopfzeile (allgemeiner Teil)
    let base_headers = [
        "Zeitstempel Erstellt",
        "Sensor IP",
        "Fortlaufender Zähler",
        "Zeitstempel Messung",
        "Highphase Messtrigger",
    ];
    let mut col: u16 = 0;
    for header in &base_headers {
        worksheet.write_string(0, col, header, None)?;
        col += 1;
    }

    // Kopfzeile (kanalspezifischer Teil)
    for ch in 0..number_of_channels {
        let ch_idx = ch as usize;
        let headers = [
            format!("Offset Start CH{}", ch_idx),
            format!("Offset Ende CH{}", ch_idx),
            format!("Kurve Start CH{}", ch_idx),
            format!("Kurve Ende CH{}", ch_idx),
            format!("Peakwert CH{}", ch_idx),
            format!("Peakposition CH{}", ch_idx),
        ];
        for header in &headers {
            worksheet.write_string(0, col, header, None)?;
            col += 1;
        }
    }

    // Datenzeilen
    for (row_idx, entry) in data.iter().enumerate() {
        let row = (row_idx + 1) as u32;

        worksheet.write_string(row, 0, &entry.created, None)?;
        worksheet.write_string(row, 1, ip, None)?;
        worksheet.write_number(row, 2, entry.counter as f64, None)?;
        worksheet.write_string(row, 3, &entry.timestamp, None)?;
        worksheet.write_number(row, 4, entry.len_trigger as f64, None)?;

        for ch in 0..number_of_channels as usize {
            let base_col = 5 + ch * 6;

            if ch < entry.offset_before.len() {
                worksheet.write_number(row, base_col as u16, entry.offset_before[ch] as f64, None)?;
            }
            if ch < entry.offset_after.len() {
                worksheet.write_number(row, (base_col + 1) as u16, entry.offset_after[ch] as f64, None)?;
            }
            if ch < entry.position_over.len() {
                worksheet.write_number(row, (base_col + 2) as u16, entry.position_over[ch] as f64, None)?;
            }
            if ch < entry.position_under.len() {
                worksheet.write_number(row, (base_col + 3) as u16, entry.position_under[ch] as f64, None)?;
            }
            if ch < entry.peak.len() {
                worksheet.write_number(row, (base_col + 4) as u16, entry.peak[ch] as f64, None)?;
            }
            if ch < entry.peak_position.len() {
                worksheet.write_number(row, (base_col + 5) as u16, entry.peak_position[ch] as f64, None)?;
            }
        }
    }

    Ok(())
}

/// Gemeinsame Export-Funktion für alle Kanalzahlen (1..=12) für Measurement (UdpTag41).
pub fn store_measurement_data_as_xlsx(
    data: &[db::UdpTag41],
    name: &str,
    ip: &str,
    number_of_channels: u8,
) -> Result<(), Box<dyn Error>> {
    if number_of_channels == 0 {
        return Ok(());
    }

    let workbook = Workbook::new(name)?;
    let mut worksheet = workbook.add_worksheet(None)?;

    // Kopfzeile (allgemeiner Teil)
    let base_headers = [
        "Zeitstempel Erstellt",
        "Sensor IP",
        "Fortlaufender Zähler",
        "Zeitstempel des letzten Offsetabgleichs",
        "Dauer des letzten Offsetabgleichs",
        "Zeitstempel Messung",
    ];
    let mut col: u16 = 0;
    for header in &base_headers {
        worksheet.write_string(0, col, header, None)?;
        col += 1;
    }

    // Kopfzeile (kanalspezifischer Teil)
    for ch in 0..number_of_channels {
        let ch_idx = ch as usize;
        let headers = [
            format!("Integral_CH{}", ch_idx),
            if ch_idx == 0 {
                // Das war im Original einmal als "Masse_CHO" geschrieben – zur Kompatibilität behalten wir das bei.
                "Masse_CHO".to_string()
            } else {
                format!("Masse_CH{}", ch_idx)
            },
            format!("Offsetwert_CH{}", ch_idx),
            format!("Offsetwert1_CH{}", ch_idx),
            format!("Offsetwert2_CH{}", ch_idx),
            format!("Grenze_Masse_unten_CH{}", ch_idx),
            format!("Grenze_Masse_oben_CH{}", ch_idx),
            format!("Status_der_Messung_CH{}", ch_idx),
        ];
        for header in &headers {
            worksheet.write_string(0, col, header, None)?;
            col += 1;
        }
    }

    // Datenzeilen
    for (row_idx, entry) in data.iter().enumerate() {
        let row = (row_idx + 1) as u32;

        worksheet.write_string(row, 0, &entry.created, None)?;
        worksheet.write_string(row, 1, ip, None)?;
        worksheet.write_number(row, 2, entry.counter as f64, None)?;
        // Spalten 3 und 4 sind im Original leer, nur die Messzeit wird geschrieben:
        worksheet.write_string(row, 5, &entry.timestamp, None)?;

        for ch in 0..number_of_channels as usize {
            let base_col = 6 + ch * 8;

            if ch < entry.integral.len() {
                worksheet.write_number(row, base_col as u16, entry.integral[ch] as f64, None)?;
            }
            if ch < entry.mass.len() {
                worksheet.write_number(row, (base_col + 1) as u16, entry.mass[ch] as f64, None)?;
            }
            if ch < entry.offset.len() {
                worksheet.write_number(row, (base_col + 2) as u16, entry.offset[ch] as f64, None)?;
            }
            if ch < entry.offset1.len() {
                worksheet.write_number(row, (base_col + 3) as u16, entry.offset1[ch] as f64, None)?;
            }
            if ch < entry.offset2.len() {
                worksheet.write_number(row, (base_col + 4) as u16, entry.offset2[ch] as f64, None)?;
            }
            if ch < entry.tolerance_bottom.len() {
                worksheet.write_number(row, (base_col + 5) as u16, entry.tolerance_bottom[ch] as f64, None)?;
            }
            if ch < entry.tolerance_top.len() {
                worksheet.write_number(row, (base_col + 6) as u16, entry.tolerance_top[ch] as f64, None)?;
            }

            if ch < entry.status.len() {
                let status_str = error_matching(&entry.status[ch]);
                worksheet.write_string(row, (base_col + 7) as u16, &status_str, None)?;
            }
        }
    }

    Ok(())
}
