-- Reset and Populate Database Script
-- This script will drop all tables, recreate them, and populate with test data

-- Drop all tables in reverse order of dependencies
DROP TABLE IF EXISTS "PostReactions";
DROP TABLE IF EXISTS "PostTags";
DROP TABLE IF EXISTS "Comments";
DROP TABLE IF EXISTS "Posts";
DROP TABLE IF EXISTS "DemotionQueue";
DROP TABLE IF EXISTS "Subscriptions";
DROP TABLE IF EXISTS "Tags";
DROP TABLE IF EXISTS "Reactions";
DROP TABLE IF EXISTS "Categories";
DROP TABLE IF EXISTS "Users";

-- Create Users table
CREATE TABLE "Users" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar,
  "bio" varchar,
  "username" varchar,
  "password" varchar,
  "profile_image_url" varchar,
  "created_on" date,
  "active" bit,
  "type" varchar
);

-- Create DemotionQueue table
CREATE TABLE "DemotionQueue" (
  "action" varchar,
  "admin_id" INTEGER,
  "approver_one_id" INTEGER,
  FOREIGN KEY(`admin_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`approver_one_id`) REFERENCES `Users`(`id`),
  PRIMARY KEY (action, admin_id, approver_one_id)
);

-- Create Subscriptions table
CREATE TABLE "Subscriptions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "follower_id" INTEGER,
  "author_id" INTEGER,
  "created_on" date,
  FOREIGN KEY(`follower_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`)
);

-- Create Posts table
CREATE TABLE "Posts" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "category_id" INTEGER,
  "title" varchar,
  "publication_date" date,
  "image_url" varchar,
  "content" varchar,
  "approved" bit,
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`)
);

-- Create Comments table
CREATE TABLE "Comments" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "author_id" INTEGER,
  "content" varchar,
  "subject" varchar,
  "created_on" date,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`),
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`)
);

-- Create Reactions table
CREATE TABLE "Reactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar,
  "image_url" varchar
);

-- Create PostReactions table
CREATE TABLE "PostReactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "reaction_id" INTEGER,
  "post_id" INTEGER,
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`),
  FOREIGN KEY(`reaction_id`) REFERENCES `Reactions`(`id`),
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`),
  UNIQUE(user_id, reaction_id, post_id)
);

-- Create Tags table
CREATE TABLE "Tags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar
);

-- Create PostTags table
CREATE TABLE "PostTags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "tag_id" INTEGER,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`),
  FOREIGN KEY(`tag_id`) REFERENCES `Tags`(`id`)
);

-- Create Categories table
CREATE TABLE "Categories" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar
);

-- ====================================
-- POPULATE DATA
-- ====================================

-- Seed Categories
INSERT INTO Categories ('label') VALUES 
('Technology'),
('Career'),
('Lifestyle'),
('Tutorial'),
('Opinion'),
('News'),
('Review'),
('Tips & Tricks');

-- Seed Tags
INSERT INTO Tags ('label') VALUES 
('JavaScript'),
('Python'),
('React'),
('Node.js'),
('CSS'),
('HTML'),
('SQL'),
('Web Development'),
('Tutorial'),
('Opinion'),
('Django'),
('TypeScript'),
('Docker'),
('DevOps'),
('Security'),
('Testing'),
('Performance'),
('Design'),
('Career Advice'),
('Productivity');

-- Seed Reactions
INSERT INTO Reactions ('label', 'image_url') VALUES 
('happy', 'https://example.com/reactions/happy.png'),
('heart', 'https://example.com/reactions/heart.png'),
('laugh', 'https://example.com/reactions/laugh.png'),
('mind-blown', 'https://example.com/reactions/mindblown.png'),
('fire', 'https://example.com/reactions/fire.png'),
('thumbs-up', 'https://example.com/reactions/thumbs-up.png'),
('celebrate', 'https://example.com/reactions/celebrate.png');

-- Seed Users (15 users with mix of admins and authors)
INSERT INTO Users ('first_name', 'last_name', 'email', 'bio', 'username', 'password', 'profile_image_url', 'created_on', 'active', 'type') 
VALUES 
('John', 'Doe', 'john@example.com', 'Software developer and tech enthusiast. Love building web applications.', 'johndoe', 'password123', 'https://example.com/users/john.jpg', '2024-01-15', 1, 'author'),
('Jane', 'Smith', 'jane@example.com', 'Full-stack developer specializing in React and Node.js', 'janesmith', 'password123', 'https://example.com/users/jane.jpg', '2024-01-20', 1, 'author'),
('Bob', 'Johnson', 'bob@example.com', 'Database administrator with 10 years of experience', 'bobjohnson', 'password123', 'https://example.com/users/bob.jpg', '2024-02-01', 1, 'admin'),
('Alice', 'Williams', 'alice@example.com', 'Frontend specialist passionate about user experience', 'alicew', 'password123', 'https://example.com/users/alice.jpg', '2024-02-05', 1, 'author'),
('Charlie', 'Brown', 'charlie@example.com', 'DevOps engineer and automation enthusiast', 'charlieb', 'password123', 'https://example.com/users/charlie.jpg', '2024-02-10', 1, 'author'),
('Emma', 'Davis', 'emma@example.com', 'Python developer and data science advocate', 'emmad', 'password123', 'https://example.com/users/emma.jpg', '2024-02-12', 1, 'author'),
('Michael', 'Wilson', 'michael@example.com', 'Security engineer focused on application security', 'michaelw', 'password123', 'https://example.com/users/michael.jpg', '2024-02-15', 1, 'author'),
('Sarah', 'Martinez', 'sarah@example.com', 'Tech writer and documentation specialist', 'sarahm', 'password123', 'https://example.com/users/sarah.jpg', '2024-02-18', 1, 'author'),
('David', 'Anderson', 'david@example.com', 'Cloud architect with AWS certification', 'davida', 'password123', 'https://example.com/users/david.jpg', '2024-02-20', 1, 'admin'),
('Lisa', 'Taylor', 'lisa@example.com', 'UI/UX designer who codes', 'lisat', 'password123', 'https://example.com/users/lisa.jpg', '2024-02-22', 1, 'author'),
('Tom', 'Moore', 'tom@example.com', 'Backend developer specializing in APIs', 'tomm', 'password123', 'https://example.com/users/tom.jpg', '2024-02-25', 1, 'author'),
('Rachel', 'White', 'rachel@example.com', 'Mobile developer exploring web technologies', 'rachelw', 'password123', 'https://example.com/users/rachel.jpg', '2024-03-01', 1, 'author'),
('Kevin', 'Harris', 'kevin@example.com', 'Systems administrator and Linux enthusiast', 'kevinh', 'password123', 'https://example.com/users/kevin.jpg', '2024-03-05', 1, 'author'),
('Amy', 'Clark', 'amy@example.com', 'Software tester and quality advocate', 'amyc', 'password123', 'https://example.com/users/amy.jpg', '2024-03-08', 1, 'author'),
('Steve', 'Lewis', 'steve@example.com', 'Tech lead with passion for mentoring', 'stevel', 'password123', 'https://example.com/users/steve.jpg', '2024-03-10', 1, 'admin');

-- Seed Posts (25 posts with variety of content)
INSERT INTO Posts ('user_id', 'category_id', 'title', 'publication_date', 'image_url', 'content', 'approved') 
VALUES 
(1, 1, 'Getting Started with Python', '2025-01-15', 'https://example.com/posts/python.jpg', 'Python is a great language for beginners. In this post, we will explore the fundamentals of Python programming including variables, data types, and control structures. Perfect for those starting their coding journey!', 1),
(1, 4, 'My Side Project Journey', '2025-01-20', 'https://example.com/posts/project.jpg', 'Here is how I built my first web app from scratch. It took 3 months of evening work, but the learning experience was invaluable. I will share my tech stack, challenges faced, and lessons learned.', 1),
(2, 1, 'React Best Practices 2025', '2025-01-25', 'https://example.com/posts/react.jpg', 'Learn the best practices for React development in 2025. We will cover component composition, state management, performance optimization, and more.', 1),
(2, 3, 'Coding Memes That Made Me Laugh', '2025-02-01', 'https://example.com/posts/memes.jpg', 'Here are my favorite coding memes from last month. Sometimes you need a good laugh during debugging sessions!', 1),
(4, 1, 'CSS Grid vs Flexbox: When to Use Each', '2025-02-05', 'https://example.com/posts/css.jpg', 'Understanding when to use CSS Grid and when to use Flexbox can be confusing. This comprehensive guide will help you choose the right tool for your layout needs.', 1),
(5, 2, 'Building a CI/CD Pipeline from Scratch', '2025-02-08', 'https://example.com/posts/cicd.jpg', 'Step-by-step guide to setting up a complete CI/CD pipeline using GitHub Actions and Docker. Automate your deployments and improve your development workflow.', 1),
(1, 1, 'Advanced SQL Queries Explained', '2025-02-10', 'https://example.com/posts/sql.jpg', 'Master complex SQL queries with these tips and examples. We will cover joins, subqueries, CTEs, and window functions.', 1),
(6, 1, 'Django vs Flask: Which to Choose?', '2025-02-12', 'https://example.com/posts/django-flask.jpg', 'A detailed comparison of Django and Flask frameworks. Learn the pros and cons of each to make an informed decision for your next project.', 1),
(7, 1, 'API Security Best Practices', '2025-02-14', 'https://example.com/posts/security.jpg', 'Secure your APIs with these essential practices. Topics include authentication, authorization, rate limiting, and input validation.', 1),
(8, 4, 'How to Write Better Documentation', '2025-02-16', 'https://example.com/posts/docs.jpg', 'Good documentation is crucial for project success. Here are my tips for writing clear, comprehensive documentation that developers will actually read.', 1),
(9, 1, 'Introduction to Docker Containers', '2025-02-18', 'https://example.com/posts/docker.jpg', 'Docker has revolutionized application deployment. This tutorial covers the basics of containerization and how to get started with Docker.', 1),
(10, 5, 'The Future of Web Development', '2025-02-20', 'https://example.com/posts/future-web.jpg', 'My thoughts on where web development is heading. From WebAssembly to edge computing, the landscape is constantly evolving.', 1),
(11, 4, 'Building RESTful APIs with Node.js', '2025-02-22', 'https://example.com/posts/rest-api.jpg', 'Complete guide to building scalable RESTful APIs using Node.js and Express. Includes code examples and best practices.', 1),
(12, 3, 'My Favorite VS Code Extensions', '2025-02-23', 'https://example.com/posts/vscode.jpg', 'Here are the VS Code extensions I cannot live without. They have boosted my productivity significantly!', 1),
(13, 8, 'Git Tips Every Developer Should Know', '2025-02-24', 'https://example.com/posts/git.jpg', 'Essential Git commands and workflows that will make your life easier. From rebasing to cherry-picking, we cover it all.', 1),
(14, 2, 'Transitioning from Junior to Senior Developer', '2025-02-24', 'https://example.com/posts/career.jpg', 'What it takes to grow from junior to senior developer. Technical skills are important, but soft skills matter too.', 1),
(2, 7, 'React Query: A Deep Dive', '2025-02-25', 'https://example.com/posts/react-query.jpg', 'React Query has changed how I handle server state in React applications. Here is everything you need to know about this powerful library.', 1),
(4, 1, 'TypeScript Tips for Beginners', '2025-02-25', 'https://example.com/posts/typescript.jpg', 'TypeScript can seem intimidating at first. These practical tips will help you get comfortable with type safety in your JavaScript projects.', 1),
(6, 8, '10 JavaScript Array Methods You Should Know', '2025-02-26', 'https://example.com/posts/array-methods.jpg', 'JavaScript array methods are powerful tools. Master these 10 methods to write cleaner, more efficient code.', 0),
(7, 4, 'Building a Todo App with React Hooks', '2025-02-26', 'https://example.com/posts/todo-app.jpg', 'Complete tutorial on building a todo application using React hooks. Perfect project for learning modern React patterns.', 0),
(8, 1, 'Understanding Async/Await in JavaScript', '2025-02-27', 'https://example.com/posts/async-await.jpg', 'Async/await makes asynchronous code easier to read and write. This guide explains how it works under the hood.', 0),
(11, 5, 'Why I Switched to Tailwind CSS', '2025-02-27', 'https://example.com/posts/tailwind.jpg', 'My experience switching from traditional CSS to Tailwind. The utility-first approach has transformed my development workflow.', 0),
(13, 2, 'Negotiating Your First Tech Job Offer', '2025-02-28', 'https://example.com/posts/negotiation.jpg', 'Tips for negotiating salary and benefits in the tech industry. Know your worth and do not be afraid to ask for what you deserve.', 1),
(14, 4, 'Introduction to GraphQL', '2025-03-01', 'https://example.com/posts/graphql.jpg', 'GraphQL is an alternative to REST that gives clients more control. Learn the basics and see if it is right for your project.', 1),
(15, 8, 'Debugging Tips That Actually Work', '2025-03-02', 'https://example.com/posts/debugging.jpg', 'Debugging can be frustrating. These proven techniques will help you find and fix bugs faster.', 1);

-- Seed Comments (40 comments across various posts)
INSERT INTO Comments ('post_id', 'author_id', 'content', 'subject', 'created_on') 
VALUES 
(1, 2, 'Great introduction! Very helpful for beginners.', 'Excellent Article', '2025-01-16'),
(1, 4, 'Thanks for sharing. I learned a lot from this.', 'Very Informative', '2025-01-17'),
(1, 6, 'Could you do a follow-up on advanced Python topics?', 'Follow-up Request', '2025-01-18'),
(2, 5, 'Inspiring story! Keep it up.', 'Motivational', '2025-01-21'),
(2, 3, 'What tech stack did you use?', 'Question', '2025-01-22'),
(2, 7, 'I am working on a similar project. This helps!', 'Related Project', '2025-01-23'),
(3, 1, 'These tips are gold. Thank you!', 'Helpful Tips', '2025-01-26'),
(3, 4, 'I disagree with point #3, but overall great article.', 'Constructive Feedback', '2025-01-27'),
(3, 8, 'Would love to see more React content from you.', 'More Please', '2025-01-28'),
(4, 1, 'Haha, the semicolon one got me!', 'Funny', '2025-02-02'),
(4, 10, 'These are too relatable!', 'So True', '2025-02-03'),
(5, 1, 'Perfect timing! I was just learning about this.', 'Perfect Timing', '2025-02-06'),
(5, 6, 'The visual examples really help understand the concepts.', 'Great Visuals', '2025-02-07'),
(5, 11, 'Can you cover CSS animations next?', 'Suggestion', '2025-02-08'),
(6, 2, 'This saved me so much time setting up my pipeline!', 'Time Saver', '2025-02-09'),
(6, 4, 'Do you have a GitHub repo with the complete setup?', 'Repo Request', '2025-02-10'),
(7, 3, 'Window functions were a game changer for me.', 'Game Changer', '2025-02-11'),
(7, 5, 'Great examples! Very practical.', 'Practical Examples', '2025-02-12'),
(8, 1, 'I have been using Flask for years. Good comparison!', 'Flask User', '2025-02-13'),
(8, 2, 'This helps me decide for my new project. Thanks!', 'Decision Help', '2025-02-14'),
(9, 4, 'Security is often overlooked. Thanks for covering this!', 'Important Topic', '2025-02-15'),
(9, 6, 'What about OAuth2? Can you cover that?', 'OAuth Question', '2025-02-16'),
(9, 12, 'Implementing these in my API right away.', 'Implementing Now', '2025-02-17'),
(10, 1, 'As a documentation writer, I approve this message!', 'Professional Approval', '2025-02-17'),
(10, 5, 'Adding diagrams makes documentation so much better.', 'Diagrams Help', '2025-02-18'),
(11, 1, 'Docker changed my development workflow completely.', 'Workflow Changed', '2025-02-19'),
(11, 3, 'The container concept clicked after reading this.', 'Concept Clicked', '2025-02-20'),
(12, 2, 'Interesting perspective on the future!', 'Thought Provoking', '2025-02-21'),
(12, 7, 'I am excited about WebAssembly too!', 'WebAssembly Fan', '2025-02-22'),
(13, 1, 'Express makes building APIs so straightforward.', 'Love Express', '2025-02-23'),
(13, 9, 'Very comprehensive tutorial. Thanks!', 'Comprehensive', '2025-02-24'),
(14, 1, 'GitLens extension is a must-have!', 'Extension Recommendation', '2025-02-24'),
(14, 4, 'I use all of these! Great list.', 'Same Here', '2025-02-25'),
(15, 2, 'Interactive rebase is so powerful once you learn it.', 'Rebase Power', '2025-02-25'),
(15, 11, 'This cleared up my confusion about merge vs rebase.', 'Cleared Confusion', '2025-02-26'),
(17, 1, 'React Query has simplified my code so much.', 'Code Simplification', '2025-02-26'),
(17, 3, 'How does it compare to Redux?', 'Comparison Question', '2025-02-27'),
(18, 2, 'TypeScript makes refactoring so much safer.', 'Refactoring Safety', '2025-02-26'),
(23, 5, 'Negotiation was scary at first but this advice helped!', 'Helpful Advice', '2025-03-01'),
(24, 2, 'GraphQL looks interesting but seems complex.', 'Looks Complex', '2025-03-02'),
(25, 1, 'The rubber duck debugging method works!', 'Rubber Duck Works', '2025-03-03');

-- Seed PostTags (many-to-many relationships)
INSERT INTO PostTags ('post_id', 'tag_id') 
VALUES 
(1, 2), (1, 9),
(2, 2), (2, 8), (2, 11),
(3, 3), (3, 8), (3, 1),
(4, 10),
(5, 5), (5, 6), (5, 8), (5, 18),
(6, 4), (6, 13), (6, 14),
(7, 7), (7, 9),
(8, 2), (8, 11),
(9, 15), (9, 8),
(10, 8), (10, 19),
(11, 13), (11, 14),
(12, 1), (12, 10),
(13, 4), (13, 8), (13, 9),
(14, 18), (14, 20),
(15, 1), (15, 20),
(16, 19),
(17, 3), (17, 1), (17, 8),
(18, 12), (18, 1), (18, 9),
(19, 1), (19, 9),
(20, 3), (20, 9),
(21, 1), (21, 9),
(22, 5), (22, 18), (22, 8),
(23, 19),
(24, 1), (24, 8),
(25, 8), (25, 20);

-- Seed PostReactions (users reacting to posts)
INSERT INTO PostReactions ('user_id', 'reaction_id', 'post_id') 
VALUES 
(2, 1, 1), (4, 1, 1), (5, 6, 1), (6, 2, 1),
(1, 2, 3), (3, 5, 3), (5, 6, 3),
(1, 3, 4), (2, 3, 4), (3, 3, 4), (10, 3, 4),
(1, 5, 5), (2, 5, 5), (11, 6, 5),
(2, 6, 6), (4, 2, 6), (9, 5, 6),
(3, 6, 7), (5, 1, 7), (8, 2, 7),
(1, 6, 8), (2, 1, 8), (5, 4, 8),
(4, 5, 9), (6, 2, 9), (12, 6, 9),
(1, 6, 10), (5, 2, 10), (8, 1, 10),
(1, 5, 11), (3, 6, 11), (7, 4, 11),
(2, 4, 12), (7, 6, 12), (13, 1, 12),
(1, 6, 13), (9, 5, 13), (11, 2, 13),
(1, 1, 14), (4, 2, 14), (10, 6, 14),
(2, 6, 15), (11, 1, 15), (13, 5, 15),
(5, 2, 16), (8, 6, 16), (14, 1, 16),
(1, 5, 17), (3, 2, 17), (9, 6, 17),
(2, 6, 18), (4, 1, 18), (7, 2, 18),
(1, 2, 23), (5, 6, 23), (14, 1, 23),
(2, 4, 24), (6, 6, 24), (9, 1, 24),
(1, 6, 25), (3, 1, 25), (14, 2, 25);

-- Seed Subscriptions (users following authors)
INSERT INTO Subscriptions ('follower_id', 'author_id', 'created_on') 
VALUES 
(2, 1, '2025-01-16'),
(4, 1, '2025-01-17'),
(5, 1, '2025-01-18'),
(6, 1, '2025-01-19'),
(1, 2, '2025-01-21'),
(4, 2, '2025-01-22'),
(7, 2, '2025-01-23'),
(1, 4, '2025-02-06'),
(2, 4, '2025-02-07'),
(1, 5, '2025-02-09'),
(3, 5, '2025-02-10'),
(1, 6, '2025-02-13'),
(2, 6, '2025-02-14'),
(8, 6, '2025-02-15'),
(4, 7, '2025-02-15'),
(6, 7, '2025-02-16'),
(1, 8, '2025-02-17'),
(5, 8, '2025-02-18'),
(2, 9, '2025-02-19'),
(7, 9, '2025-02-20'),
(2, 10, '2025-02-21'),
(10, 11, '2025-02-24'),
(11, 13, '2025-02-26'),
(12, 13, '2025-02-27'),
(5, 14, '2025-02-28');

-- Seed DemotionQueue (admin demotion requests)
INSERT INTO DemotionQueue ('action', 'admin_id', 'approver_one_id') 
VALUES 
('demote', 9, 3),
('demote', 15, 3);

-- Run This to Add profile_image blobs
ALTER TABLE Users
ADD COLUMN profile_image BLOB;

ALTER TABLE Posts
ADD COLUMN image BLOB;

UPDATE Posts
SET approved = 1
WHERE approved = 'true';

ALTER TABLE Users
ADD COLUMN updated_at date;

ALTER TABLE Posts
ADD COLUMN updated_at date;


UPDATE Users
SET updated_at = created_on
WHERE updated_at IS NULL;

UPDATE Posts
SET updated_at = publication_date;

WHERE updated_at IS NULL;

ALTER TABLE Reactions
RENAME COLUMN image_url TO emoji;


  const reactionEmojis = {
    "happy": "😊",
    "heart": "❤️",
    "laugh": "😂",
    "mind-blown": "🤯",
    "fire": "🔥",
    "thumbs-up": "👍",
    "celebrate": "🎉"
  }


CREATE UNIQUE INDEX idx_unique_user_reaction_post 
ON PostReactions(user_id, reaction_id, post_id);

UPDATE Users
SET type = 'admin'
WHERE id = 16