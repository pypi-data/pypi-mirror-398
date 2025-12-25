use std::error::Error;
use pyo3::prelude::*;
use once_cell::sync::Lazy;

mod export;
mod db;
mod process;

/// Globaler Tokio-Runtime, damit nicht bei jedem Python‑Call
/// eine neue Runtime erstellt werden muss (sehr teuer).
static TOKIO_RUNTIME: Lazy<tokio::runtime::Runtime> = Lazy::new(|| {
    tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()
        .expect("Failed to create Tokio runtime")
});

fn tokio_runtime() -> &'static tokio::runtime::Runtime {
    &*TOKIO_RUNTIME
}

#[pymodule]
fn sdb_connector(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(select_additional_info_data, m)?)?;
    m.add_function(wrap_pyfunction!(select_measurement_data, m)?)?;
    m.add_function(wrap_pyfunction!(select_raw_data, m)?)?;
    m.add_function(wrap_pyfunction!(select_ai_data, m)?)?;
    m.add_function(wrap_pyfunction!(select_di_data, m)?)?;
    // m.add_function(wrap_pyfunction!(select_general_info_data, m)?)?;
    Ok(())
}

#[pyfunction]
fn select_ai_data(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> PyResult<Vec<(u8, u8, String, u16, u64)>> {
    let rt = tokio_runtime();
    let data = match rt.block_on(select_ai_data_async(
        ip,
        port,
        user,
        pw,
        namespace,
        db_name,
        table_name,
        run_id,
        path_name,
        select_type,
    )) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting AI data: {:?}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Error selecting AI data: {e}"
            )));
        }
    };
    Ok(data)
}

#[pyfunction]
fn select_di_data(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> PyResult<Vec<(u8, u8, String, bool, u64)>> {
    let rt = tokio_runtime();
    let data = match rt.block_on(select_di_data_async(
        ip,
        port,
        user,
        pw,
        namespace,
        db_name,
        table_name,
        run_id,
        path_name,
        select_type,
    )) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting DI data: {:?}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Error selecting DI data: {e}"
            )));
        }
    };
    Ok(data)
}

#[pyfunction]
fn select_additional_info_data(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> PyResult<Vec<(u64, u16, u8, u16, u16, u16, u16, u16, u16, String)>> {
    let rt = tokio_runtime();
    let data = match rt.block_on(select_additional_info_data_async(
        ip,
        port,
        user,
        pw,
        namespace,
        db_name,
        table_name,
        run_id,
        path_name,
        select_type,
    )) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting additional info data: {:?}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Error selecting additional info data: {e}"
            )));
        }
    };
    Ok(data)
}

#[pyfunction]
fn select_measurement_data(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> PyResult<Vec<(u64, u8, u64, u64, u16, u16, u16, u16, u16, String, Vec<String>)>> {
    let rt = tokio_runtime();
    let data = match rt.block_on(select_measurement_data_async(
        ip,
        port,
        user,
        pw,
        namespace,
        db_name,
        table_name,
        run_id,
        path_name,
        select_type,
    )) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting measurement data: {:?}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Error selecting measurement data: {e}"
            )));
        }
    };
    Ok(data)
}

#[pyfunction]
fn select_raw_data(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
) -> PyResult<Vec<(u64, u8, i32, String, u32)>> {
    let rt = tokio_runtime();
    let data = match rt.block_on(select_raw_data_async(
        ip, port, user, pw, namespace, db_name, table_name, run_id,
    )) {
        Ok(data) => data,
        Err(e) => {
            eprintln!("Error selecting raw data: {:?}", e);
            return Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!(
                "Error selecting raw data: {e}"
            )));
        }
    };
    Ok(data)
}

// --- Async‑Helper, die die eigentliche Arbeit machen ---------------------

pub async fn select_ai_data_async(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> Result<Vec<(u8, u8, String, u16, u64)>, Box<dyn Error>> {
    let db = db::connect_to_db(ip, port, user, pw, namespace, db_name).await?;
    let result = db::query_ai_data(&db, table_name, run_id).await?;
    let data = process::process_ai_data(result, path_name, select_type).await?;
    Ok(data)
}

pub async fn select_di_data_async(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> Result<Vec<(u8, u8, String, bool, u64)>, Box<dyn Error>> {
    let db = db::connect_to_db(ip, port, user, pw, namespace, db_name).await?;
    let result = db::query_di_data(&db, table_name, run_id).await?;
    let data = process::process_di_data(result, path_name, select_type).await?;
    Ok(data)
}

pub async fn select_additional_info_data_async(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> Result<Vec<(u64, u16, u8, u16, u16, u16, u16, u16, u16, String)>, Box<dyn Error>> {
    let db = db::connect_to_db(ip, port, user, pw, namespace, db_name).await?;

    // Allgemeine Sensor‑Infos holen (IP + Kanalanzahl)
    let general_info = db::query_amv_static_info(&db, "amv_static_info", run_id).await?;
    let info = match general_info.first() {
        Some(info) => info,
        None => {
            return Err("amv_static_info: no matching entry for run_id and no fallback row".into());
        }
    };

    let ip = format!(
        "{}.{}.{}.{}",
        info.ip_address[0], info.ip_address[1], info.ip_address[2], info.ip_address[3]
    );
    let number_of_channels = info.number_of_channels;

    let result = db::query_additonal_info_data(&db, table_name, run_id).await?;
    let data = process::process_additonal_info_data(
        result,
        &ip,
        path_name,
        select_type,
        number_of_channels,
    )
    .await?;
    Ok(data)
}

pub async fn select_measurement_data_async(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
    path_name: &str,
    select_type: u8,
) -> Result<
    Vec<(u64, u8, u64, u64, u16, u16, u16, u16, u16, String, Vec<String>)>,
    Box<dyn Error>,
> {
    let db = db::connect_to_db(ip, port, user, pw, namespace, db_name).await?;

    // Allgemeine Sensor‑Infos holen (IP + Kanalanzahl)
    let general_info = db::query_amv_static_info(&db, "amv_static_info", run_id).await?;
    let info = match general_info.first() {
        Some(info) => info,
        None => {
            return Err("amv_static_info: no matching entry for run_id and no fallback row".into());
        }
    };

    let ip = format!(
        "{}.{}.{}.{}",
        info.ip_address[0], info.ip_address[1], info.ip_address[2], info.ip_address[3]
    );
    let number_of_channels = info.number_of_channels;

    let result = db::query_measurement_data(&db, table_name, run_id).await?;
    let data = process::process_measurement_data(
        result,
        &ip,
        path_name,
        select_type,
        number_of_channels,
    )
    .await?;
    Ok(data)
}

pub async fn select_raw_data_async(
    ip: &str,
    port: &str,
    user: &str,
    pw: &str,
    namespace: &str,
    db_name: &str,
    table_name: &str,
    run_id: &str,
) -> Result<Vec<(u64, u8, i32, String, u32)>, Box<dyn Error>> {
    let db = db::connect_to_db(ip, port, user, pw, namespace, db_name).await?;
    let result = db::query_raw_data(&db, table_name, run_id).await?;
    let data = process::process_raw_data(result).await?;
    Ok(data)
}
