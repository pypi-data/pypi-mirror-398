fn main() {
    if std::env::var_os("CARGO_FEATURE_PYTHON").is_some() {
        pyo3_build_config::add_python_framework_link_args();
    }
}
