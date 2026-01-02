use pyo3::prelude::*;
use std::time::Duration;

#[pyfunction]
fn hello() -> &'static str {
    "hello from pyrust (native)"
}

#[pyfunction]
fn add(a: i64, b: i64) -> i64 {
    a + b
}

#[pyfunction]
fn sum_vector(py: Python<'_>, values: Vec<i64>) -> PyResult<i64> {
    let result = py.allow_threads(|| {
        let mut total: i64 = 0;
        for value in values {
            total += value;
        }
        total
    });
    Ok(result)
}

#[pyfunction]
fn scale_vec(py: Python<'_>, values: Vec<f64>, factor: f64) -> PyResult<Vec<f64>> {
    let result = py.allow_threads(|| {
        let mut output: Vec<f64> = Vec::with_capacity(values.len());
        for value in values {
            if value > 0.0 {
                output.push(value * factor);
            } else {
                output.push(value);
            }
        }
        output
    });
    Ok(result)
}

#[pyfunction]
fn filter_and_double(py: Python<'_>, mut values: Vec<i64>, threshold: i64) -> PyResult<Vec<i64>> {
    let result = py.allow_threads(|| {
        for value in &mut values {
            if *value > threshold {
                *value *= 2;
            } else if *value % 2 == 0 {
                *value += 1;
            }
        }
        values
    });
    Ok(result)
}

#[pyfunction]
fn accumulate_alternating(values: Vec<f64>) -> PyResult<Vec<f64>> {
    let mut running_total = 0.0;
    let mut output: Vec<f64> = Vec::with_capacity(values.len());
    for (index, value) in values.into_iter().enumerate() {
        if index % 2 == 0 {
            running_total += value;
        } else {
            running_total -= value;
        }
        output.push(running_total);
    }
    Ok(output)
}

#[pyfunction]
fn conditional_step(value: i64, increment: bool) -> i64 {
    if increment {
        value + 1
    } else {
        value - 1
    }
}

#[pyfunction]
fn average_or_zero(values: Vec<f64>) -> f64 {
    if values.is_empty() {
        return 0.0;
    }
    let sum: f64 = values.iter().sum();
    sum / values.len() as f64
}

#[pyfunction]
fn slow_transform(py: Python<'_>, values: Vec<i64>, delay_ms: u64) -> PyResult<Vec<i64>> {
    let result = py.allow_threads(|| {
        std::thread::sleep(Duration::from_millis(delay_ms));
        values
            .into_iter()
            .map(|value| value * 3)
            .collect::<Vec<i64>>()
    });
    Ok(result)
}

#[pyfunction]
fn slow_average(values: Vec<f64>, delay_ms: u64) -> PyResult<f64> {
    std::thread::sleep(Duration::from_millis(delay_ms));
    if values.is_empty() {
        Ok(0.0)
    } else {
        let sum: f64 = values.iter().sum();
        Ok(sum / values.len() as f64)
    }
}

/// The module name must match `tool.maturin.module-name` in `pyproject.toml`
#[pymodule]
fn _native(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello, m)?)?;
    m.add_function(wrap_pyfunction!(add, m)?)?;
    m.add_function(wrap_pyfunction!(sum_vector, m)?)?;
    m.add_function(wrap_pyfunction!(scale_vec, m)?)?;
    m.add_function(wrap_pyfunction!(filter_and_double, m)?)?;
    m.add_function(wrap_pyfunction!(accumulate_alternating, m)?)?;
    m.add_function(wrap_pyfunction!(conditional_step, m)?)?;
    m.add_function(wrap_pyfunction!(average_or_zero, m)?)?;
    m.add_function(wrap_pyfunction!(slow_transform, m)?)?;
    m.add_function(wrap_pyfunction!(slow_average, m)?)?;
    Ok(())
}
