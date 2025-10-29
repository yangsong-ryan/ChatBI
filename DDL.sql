-- 创建projects表
CREATE TABLE projects (
    id INT AUTO_INCREMENT PRIMARY KEY,
    project_name VARCHAR(100) NOT NULL,
    budget DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_project_name (project_name)
);

-- 插入测试数据
INSERT INTO projects (project_name, budget) VALUES
('北极星计划', 1500000.00),
('天宫项目', 2800000.50),
('银河工程', 750000.75),
('凤凰计划', 3200000.25),
('龙腾项目', 1950000.80)
;

-- 验证数据插入
SELECT * FROM projects;