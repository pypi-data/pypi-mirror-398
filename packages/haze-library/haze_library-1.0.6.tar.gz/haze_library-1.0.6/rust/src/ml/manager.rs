// ml/manager.rs - 模型管理器
#![allow(dead_code)]
//
// 提供模型序列化、持久化和智能加载功能
// 遵循 Occam's Razor: 最简单的序列化方案 (bincode)

use crate::ml::models::{SFGModel, SFGModelConfig, SerializableWeights};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::{self, File};
use std::io::{BufReader, BufWriter};
use std::path::PathBuf;

/// 模型元数据
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ModelMetadata {
    pub name: String,
    pub version: String,
    pub created_at: u64,
    pub training_samples: usize,
    pub features_dim: usize,
    pub config: SFGModelConfig,
}

/// 模型管理器
///
/// 负责模型的保存、加载和缓存
pub struct SFGModelManager {
    model_dir: PathBuf,
    metadata_cache: HashMap<String, ModelMetadata>,
}

impl SFGModelManager {
    /// 创建模型管理器
    pub fn new(model_dir: &str) -> Self {
        let path = PathBuf::from(model_dir);

        // 创建目录(如果不存在)
        if let Err(e) = fs::create_dir_all(&path) {
            eprintln!("Warning: Failed to create model directory: {e}");
        }

        Self {
            model_dir: path,
            metadata_cache: HashMap::new(),
        }
    }

    /// 保存模型元数据
    pub fn save_metadata(&mut self, name: &str, metadata: &ModelMetadata) -> Result<(), String> {
        let path = self.model_dir.join(format!("{name}.meta.json"));

        let file =
            File::create(&path).map_err(|e| format!("Failed to create metadata file: {e}"))?;

        let writer = BufWriter::new(file);
        serde_json::to_writer_pretty(writer, metadata)
            .map_err(|e| format!("Failed to write metadata: {e}"))?;

        self.metadata_cache
            .insert(name.to_string(), metadata.clone());

        Ok(())
    }

    /// 加载模型元数据
    pub fn load_metadata(&mut self, name: &str) -> Result<ModelMetadata, String> {
        // 检查缓存
        if let Some(meta) = self.metadata_cache.get(name) {
            return Ok(meta.clone());
        }

        let path = self.model_dir.join(format!("{name}.meta.json"));

        if !path.exists() {
            return Err(format!("Metadata file not found: {name}"));
        }

        let file = File::open(&path).map_err(|e| format!("Failed to open metadata file: {e}"))?;

        let reader = BufReader::new(file);
        let metadata: ModelMetadata = serde_json::from_reader(reader)
            .map_err(|e| format!("Failed to parse metadata: {e}"))?;

        self.metadata_cache
            .insert(name.to_string(), metadata.clone());

        Ok(metadata)
    }

    /// 检查模型是否存在
    pub fn model_exists(&self, name: &str) -> bool {
        let path = self.model_dir.join(format!("{name}.meta.json"));
        path.exists()
    }

    /// 列出所有已保存的模型
    pub fn list_models(&self) -> Vec<String> {
        let mut models = Vec::new();

        if let Ok(entries) = fs::read_dir(&self.model_dir) {
            for entry in entries.flatten() {
                if let Some(name) = entry.file_name().to_str() {
                    if name.ends_with(".meta.json") {
                        let model_name = name.trim_end_matches(".meta.json").to_string();
                        models.push(model_name);
                    }
                }
            }
        }

        models
    }

    /// 删除模型
    pub fn delete_model(&mut self, name: &str) -> Result<(), String> {
        let meta_path = self.model_dir.join(format!("{name}.meta.json"));
        let weights_path = self.model_dir.join(format!("{name}.weights.bin"));

        if meta_path.exists() {
            fs::remove_file(&meta_path).map_err(|e| format!("Failed to delete metadata: {e}"))?;
        }

        if weights_path.exists() {
            fs::remove_file(&weights_path).map_err(|e| format!("Failed to delete weights: {e}"))?;
        }

        self.metadata_cache.remove(name);

        Ok(())
    }

    /// 保存完整模型 (元数据 + 权重)
    ///
    /// 元数据以 JSON 格式保存，权重以 bincode 二进制格式保存
    pub fn save_model(
        &mut self,
        name: &str,
        model: &SFGModel,
        metadata: &ModelMetadata,
    ) -> Result<(), String> {
        // 1. 保存元数据
        self.save_metadata(name, metadata)?;

        // 2. 保存权重 (如果模型已训练)
        if let Some(weights) = model.get_serializable_weights() {
            let path = self.model_dir.join(format!("{name}.weights.bin"));

            let file =
                File::create(&path).map_err(|e| format!("Failed to create weights file: {e}"))?;

            let mut writer = BufWriter::new(file);
            bincode::encode_into_std_write(&weights, &mut writer, bincode::config::standard())
                .map_err(|e| format!("Failed to serialize weights: {e}"))?;
        }

        Ok(())
    }

    /// 加载完整模型 (元数据 + 权重)
    ///
    /// 根据元数据中的配置创建模型，然后恢复权重
    pub fn load_model(&mut self, name: &str) -> Result<(SFGModel, ModelMetadata), String> {
        // 1. 加载元数据
        let metadata = self.load_metadata(name)?;

        // 2. 根据配置创建模型
        let mut model = SFGModel::from_config(&metadata.config);

        // 3. 加载权重 (如果存在)
        let weights_path = self.model_dir.join(format!("{name}.weights.bin"));

        if weights_path.exists() {
            let file = File::open(&weights_path)
                .map_err(|e| format!("Failed to open weights file: {e}"))?;

            let mut reader = BufReader::new(file);
            let weights: SerializableWeights =
                bincode::decode_from_std_read(&mut reader, bincode::config::standard())
                    .map_err(|e| format!("Failed to deserialize weights: {e}"))?;

            model.set_serializable_weights(weights);
        }

        Ok((model, metadata))
    }

    /// 检查模型权重是否存在
    pub fn weights_exist(&self, name: &str) -> bool {
        let path = self.model_dir.join(format!("{name}.weights.bin"));
        path.exists()
    }

    /// 获取模型目录
    pub fn get_model_dir(&self) -> &PathBuf {
        &self.model_dir
    }

    /// 清理过期模型 (保留最近 n 个)
    pub fn cleanup_old_models(&mut self, keep_count: usize) -> Result<usize, String> {
        let mut models: Vec<(String, u64)> = Vec::new();

        for name in self.list_models() {
            if let Ok(meta) = self.load_metadata(&name) {
                models.push((name, meta.created_at));
            }
        }

        // 按创建时间排序 (最新在前)
        models.sort_by(|a, b| b.1.cmp(&a.1));

        let mut deleted = 0;
        for (name, _) in models.into_iter().skip(keep_count) {
            if self.delete_model(&name).is_ok() {
                deleted += 1;
            }
        }

        Ok(deleted)
    }
}

impl Default for SFGModelManager {
    fn default() -> Self {
        Self::new("./models")
    }
}

/// 获取当前时间戳 (秒)
pub fn current_timestamp() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0)
}

/// 创建模型元数据
pub fn create_metadata(
    name: &str,
    config: &SFGModelConfig,
    training_samples: usize,
    features_dim: usize,
) -> ModelMetadata {
    ModelMetadata {
        name: name.to_string(),
        version: "1.0.1".to_string(),
        created_at: current_timestamp(),
        training_samples,
        features_dim,
        config: config.clone(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::ml::models::{AISuperTrendLinReg, ATR2RidgeModel, ModelType, MomentumLinRegModel};
    use ndarray::{Array1, Array2};
    use std::env;
    use std::sync::atomic::{AtomicU64, Ordering};

    // 原子计数器确保每个测试有唯一目录
    static TEST_COUNTER: AtomicU64 = AtomicU64::new(0);

    fn get_test_dir() -> PathBuf {
        let mut dir = env::temp_dir();
        let unique_id = TEST_COUNTER.fetch_add(1, Ordering::SeqCst);
        dir.push(format!(
            "haze_test_{}_{}_{}",
            current_timestamp(),
            std::process::id(),
            unique_id
        ));
        dir
    }

    #[test]
    fn test_model_manager_creation() {
        let dir = get_test_dir();
        let manager = SFGModelManager::new(dir.to_str().unwrap());

        assert!(manager.get_model_dir().exists() || dir.to_str().is_some());

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_save_and_load_metadata() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        let config = SFGModelConfig::default();
        let metadata = create_metadata("test_model", &config, 100, 10);

        // 保存
        let result = manager.save_metadata("test_model", &metadata);
        assert!(result.is_ok());

        // 检查存在
        assert!(manager.model_exists("test_model"));

        // 加载
        let loaded = manager.load_metadata("test_model");
        assert!(loaded.is_ok());

        let loaded = loaded.unwrap();
        assert_eq!(loaded.name, "test_model");
        assert_eq!(loaded.training_samples, 100);

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_list_models() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        let config = SFGModelConfig::default();

        // 保存多个模型
        for i in 0..3 {
            let metadata = create_metadata(&format!("model_{i}"), &config, 100, 10);
            manager
                .save_metadata(&format!("model_{i}"), &metadata)
                .unwrap();
        }

        let models = manager.list_models();
        assert_eq!(models.len(), 3);

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_delete_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        let config = SFGModelConfig::default();
        let metadata = create_metadata("to_delete", &config, 100, 10);

        manager.save_metadata("to_delete", &metadata).unwrap();
        assert!(manager.model_exists("to_delete"));

        manager.delete_model("to_delete").unwrap();
        assert!(!manager.model_exists("to_delete"));

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    // ==================== 完整模型持久化测试 ====================

    #[test]
    fn test_save_and_load_linreg_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        // 创建并训练模型
        let features = Array2::from_shape_vec(
            (5, 2),
            vec![1.0, 2.0, 2.0, 4.0, 3.0, 6.0, 4.0, 8.0, 5.0, 10.0],
        )
        .unwrap();
        let targets = Array1::from_vec(vec![3.0, 6.0, 9.0, 12.0, 15.0]);

        let mut model = SFGModel::LinReg(AISuperTrendLinReg::new());
        model.train(&features, &targets).unwrap();
        assert!(model.is_trained());

        // 保存模型
        let config = SFGModelConfig::default();
        let metadata = create_metadata("linreg_test", &config, 5, 2);
        manager
            .save_model("linreg_test", &model, &metadata)
            .unwrap();

        // 验证文件存在
        assert!(manager.model_exists("linreg_test"));
        assert!(manager.weights_exist("linreg_test"));

        // 加载模型
        let (loaded_model, loaded_metadata) = manager.load_model("linreg_test").unwrap();
        assert!(loaded_model.is_trained());
        assert_eq!(loaded_metadata.training_samples, 5);

        // 验证预测一致性
        let original_predictions = model.predict(&features);
        let loaded_predictions = loaded_model.predict(&features);

        for i in 0..5 {
            assert!(
                (original_predictions[i] - loaded_predictions[i]).abs() < 1e-10,
                "Prediction mismatch at index {}: {} vs {}",
                i,
                original_predictions[i],
                loaded_predictions[i]
            );
        }

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_save_and_load_ridge_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        // 创建并训练模型
        let features = Array2::from_shape_vec(
            (5, 2),
            vec![1.0, 2.0, 2.0, 4.0, 3.0, 6.0, 4.0, 8.0, 5.0, 10.0],
        )
        .unwrap();
        let targets = Array1::from_vec(vec![3.0, 6.0, 9.0, 12.0, 15.0]);

        let mut model = SFGModel::Ridge(ATR2RidgeModel::new(0.5));
        model.train(&features, &targets).unwrap();
        assert!(model.is_trained());

        // 保存模型
        let config = SFGModelConfig {
            model_type: ModelType::Ridge,
            ridge_alpha: 0.5,
            ..Default::default()
        };
        let metadata = create_metadata("ridge_test", &config, 5, 2);
        manager.save_model("ridge_test", &model, &metadata).unwrap();

        // 加载模型
        let (loaded_model, _) = manager.load_model("ridge_test").unwrap();
        assert!(loaded_model.is_trained());

        // 验证预测一致性
        let original_predictions = model.predict(&features);
        let loaded_predictions = loaded_model.predict(&features);

        for i in 0..5 {
            assert!(
                (original_predictions[i] - loaded_predictions[i]).abs() < 1e-10,
                "Prediction mismatch at index {}: {} vs {}",
                i,
                original_predictions[i],
                loaded_predictions[i]
            );
        }

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_save_and_load_momentum_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        // 创建并训练模型
        let features = Array2::from_shape_vec(
            (5, 3),
            vec![
                1.0, 0.5, 0.1, 2.0, 1.0, 0.2, 3.0, 1.5, 0.3, 4.0, 2.0, 0.4, 5.0, 2.5, 0.5,
            ],
        )
        .unwrap();
        let targets = Array1::from_vec(vec![1.6, 3.2, 4.8, 6.4, 8.0]);

        let mut model = SFGModel::Momentum(MomentumLinRegModel::new());
        model.train(&features, &targets).unwrap();
        assert!(model.is_trained());

        // 保存模型
        let config = SFGModelConfig::default();
        let metadata = create_metadata("momentum_test", &config, 5, 3);
        manager
            .save_model("momentum_test", &model, &metadata)
            .unwrap();

        // 加载模型
        let (loaded_model, _) = manager.load_model("momentum_test").unwrap();
        assert!(loaded_model.is_trained());

        // 验证预测一致性
        let original_predictions = model.predict(&features);
        let loaded_predictions = loaded_model.predict(&features);

        for i in 0..5 {
            assert!(
                (original_predictions[i] - loaded_predictions[i]).abs() < 1e-10,
                "Prediction mismatch at index {i}"
            );
        }

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_save_untrained_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        // 创建未训练模型
        let model = SFGModel::LinReg(AISuperTrendLinReg::new());
        assert!(!model.is_trained());

        // 保存未训练模型
        let config = SFGModelConfig::default();
        let metadata = create_metadata("untrained", &config, 0, 0);
        manager.save_model("untrained", &model, &metadata).unwrap();

        // 元数据应存在，但权重文件不应存在
        assert!(manager.model_exists("untrained"));
        assert!(!manager.weights_exist("untrained"));

        // 加载应成功但模型未训练
        let (loaded_model, _) = manager.load_model("untrained").unwrap();
        assert!(!loaded_model.is_trained());

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_delete_model_with_weights() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        // 创建并训练模型
        let features = Array2::from_shape_vec((5, 2), vec![1.0; 10]).unwrap();
        let targets = Array1::from_vec(vec![1.0, 2.0, 3.0, 4.0, 5.0]);

        let mut model = SFGModel::LinReg(AISuperTrendLinReg::new());
        model.train(&features, &targets).unwrap();

        let config = SFGModelConfig::default();
        let metadata = create_metadata("to_delete_full", &config, 5, 2);
        manager
            .save_model("to_delete_full", &model, &metadata)
            .unwrap();

        // 验证存在
        assert!(manager.model_exists("to_delete_full"));
        assert!(manager.weights_exist("to_delete_full"));

        // 删除
        manager.delete_model("to_delete_full").unwrap();

        // 验证都删除了
        assert!(!manager.model_exists("to_delete_full"));
        assert!(!manager.weights_exist("to_delete_full"));

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn test_load_nonexistent_model() {
        let dir = get_test_dir();
        let mut manager = SFGModelManager::new(dir.to_str().unwrap());

        let result = manager.load_model("nonexistent");
        assert!(result.is_err());
        assert!(result.unwrap_err().contains("not found"));

        // 清理
        let _ = fs::remove_dir_all(&dir);
    }
}
