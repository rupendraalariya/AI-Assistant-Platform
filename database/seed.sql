-- Seed data for development/testing

-- Create admin user (password: admin123456)
INSERT INTO users (email, username, hashed_password, role) VALUES
('admin@chatbot.com', 'admin', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOoGz3.Y3pE3EZzRTECAm5GCzFHBLwXHe', 'admin')
ON CONFLICT (email) DO NOTHING;

-- Create test user (password: testuser123)
INSERT INTO users (email, username, hashed_password, role) VALUES
('test@chatbot.com', 'testuser', '$2b$12$LQv3c1yqBo9SkvXS7QTJPOoGz3.Y3pE3EZzRTECAm5GCzFHBLwXHe', 'user')
ON CONFLICT (email) DO NOTHING;
