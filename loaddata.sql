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
  "created_on" datetime DEFAULT (datetime('now')),
  "active" bit,
  "type" varchar,
  "profile_image" BLOB,
  "updated_at" datetime DEFAULT (datetime('now'))
);

CREATE TRIGGER users_set_updated_at
AFTER UPDATE ON Users
FOR EACH ROW
BEGIN
    UPDATE Users SET updated_at = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER users_protect_created_on
BEFORE UPDATE OF created_on ON Users
FOR EACH ROW
BEGIN
    SELECT RAISE(ABORT, 'created_on cannot be modified');
END;

CREATE TRIGGER users_block_delete_last_admin
BEFORE DELETE ON Users
WHEN OLD.type = 'admin'
  AND (SELECT COUNT(*) FROM Users WHERE type = 'admin' AND id <> OLD.id) = 0
BEGIN
  SELECT RAISE(ABORT, 'Cannot delete the last admin');
END;

CREATE TRIGGER users_block_deactivate_last_admin
BEFORE UPDATE OF active ON Users
WHEN OLD.type = 'admin' AND OLD.active = 1 AND NEW.active = 0
  AND (SELECT COUNT(*) FROM Users WHERE type = 'admin' AND id <> OLD.id) = 0
BEGIN
  SELECT RAISE(ABORT, 'Cannot deactivate the last admin');
END;

CREATE TRIGGER users_block_demote_last_admin
BEFORE UPDATE OF type ON Users
WHEN OLD.type = 'admin' AND NEW.type = 'author'
  AND (SELECT COUNT(*) FROM Users WHERE type = 'admin' AND id <> OLD.id) = 0
BEGIN
  SELECT RAISE(ABORT, 'Cannot demote the last admin');
END;

CREATE TRIGGER users_demote_admin_on_deactivate
AFTER UPDATE OF active ON Users
WHEN OLD.active = 1 AND NEW.active = 0 AND NEW.type = 'admin'
BEGIN
  UPDATE Users SET type = 'author' WHERE id = NEW.id;
END;

CREATE TRIGGER users_block_inactive_admin_promotion
BEFORE UPDATE OF type ON Users
WHEN NEW.type = 'admin' AND OLD.type = 'author' AND NEW.active = 0
BEGIN
  SELECT RAISE(ABORT, 'Must activate user before promoting to admin');
END;

CREATE TRIGGER users_block_duplicate_password
BEFORE UPDATE OF password ON Users
WHEN OLD.password = NEW.password
BEGIN
    SELECT RAISE(ABORT, 'Cannot use same password');
END;

CREATE TABLE "DemotionQueue" (
  "action" varchar,
  "admin_id" INTEGER,
  "approver_one_id" INTEGER,
  FOREIGN KEY(`admin_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`approver_one_id`) REFERENCES `Users`(`id`),
  PRIMARY KEY (action, admin_id, approver_one_id),
  UNIQUE(action, admin_id)
);

CREATE TABLE "Subscriptions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "follower_id" INTEGER,
  "author_id" INTEGER,
  "created_on" datetime,
  FOREIGN KEY(`follower_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE,
  UNIQUE(follower_id, author_id)
);

CREATE TABLE "Posts" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "category_id" INTEGER,
  "title" varchar,
  "publication_date" datetime,
  "content" varchar,
  "status" varchar DEFAULT 'draft',
  "submitted_at" datetime,
  "reviewed_at" datetime,
  "reviewer_id" INTEGER,
  "admin_comments" varchar,
  "updated_at" datetime DEFAULT (datetime('now')),
  "image" BLOB,
  "created_on" datetime DEFAULT (datetime('now')),
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`reviewer_id`) REFERENCES `Users`(`id`)
);


CREATE TRIGGER posts_add_publication_date_on_approved
AFTER UPDATE OF status ON Posts
WHEN OLD.status IS NOT NEW.status AND NEW.status = 'approved'
BEGIN
  UPDATE Posts SET publication_date = datetime('now') WHERE id = NEW.id;
END;

CREATE TRIGGER posts_reset_publication_date_on_depublish
AFTER UPDATE OF status ON Posts
WHEN OLD.status IS NOT NEW.status AND NEW.status != 'approved'
BEGIN
  UPDATE POSTS SET publication_date = NULL WHERE id = NEW.id;
END;

CREATE TABLE "Comments" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "author_id" INTEGER,
  "content" varchar,
  "subject" varchar,
  "created_on" datetime,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`author_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE
);

CREATE TABLE "Reactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar,
  "emoji" varchar UNIQUE
);

CREATE TABLE "PostReactions" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "user_id" INTEGER,
  "reaction_id" INTEGER,
  "post_id" INTEGER,
  FOREIGN KEY(`user_id`) REFERENCES `Users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`reaction_id`) REFERENCES `Reactions`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`) ON DELETE CASCADE,
  UNIQUE(user_id, reaction_id, post_id)
);

CREATE TABLE "Tags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar,
  UNIQUE(label)
);

CREATE TABLE "PostTags" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "post_id" INTEGER,
  "tag_id" INTEGER,
  FOREIGN KEY(`post_id`) REFERENCES `Posts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY(`tag_id`) REFERENCES `Tags`(`id`) ON DELETE CASCADE,
  UNIQUE(post_id, tag_id)
);

CREATE TABLE "Categories" (
  "id" INTEGER PRIMARY KEY AUTOINCREMENT,
  "label" varchar
);

-- ====================================
-- SEED DATA
-- ====================================

-- Seed Users
INSERT INTO Users (first_name, last_name, email, bio, username, password, created_on, active, type)
VALUES
  ('John',    'Doe',      'john@example.com',          'Software developer and tech enthusiast. Love building web applications.', 'johndoe',     'password123', '2024-01-15', 1, 'admin'),
  ('Jane',    'Smith',    'jane@example.com',           'Full-stack developer specializing in React and Node.js',                  'janesmith',   'password123', '2024-01-20', 1, 'admin'),
  ('Bob',     'Johnson',  'bob@example.com',            'Database administrator with 10 years of experience',                     'bobjohnson',  'password123', '2024-02-01', 1, 'admin'),
  ('Alice',   'Williams', 'alice@example.com',          'Frontend specialist passionate about user experience',                   'alicew',      'password123', '2024-02-05', 1, 'author'),
  ('Charlie', 'Brown',    'charlie@example.com',        'DevOps engineer and automation enthusiast',                              'charlieb',    'password123', '2024-02-10', 1, 'author'),
  ('Emma',    'Davis',    'emma@example.com',           'Python developer and data science advocate',                             'emmad',       'password123', '2024-02-12', 1, 'author'),
  ('Michael', 'Wilson',   'michael@example.com',        'Security engineer focused on application security',                     'michaelw',    'password123', '2024-02-15', 1, 'author'),
  ('Sarah',   'Martinez', 'sarah@example.com',          'Tech writer and documentation specialist',                              'sarahm',      'password123', '2024-02-18', 1, 'author'),
  ('David',   'Anderson', 'david@example.com',          'Cloud architect with AWS certification',                                'davida',      'password123', '2024-02-20', 1, 'author'),
  ('Lisa',    'Taylor',   'lisa@example.com',           'UI/UX designer who codes',                                              'lisat',       'password123', '2024-02-22', 1, 'author'),
  ('Tom',     'Moore',    'tom@example.com',            'Backend developer specializing in APIs',                                'tomm',        'password123', '2024-02-25', 1, 'author'),
  ('Rachel',  'White',    'rachel@example.com',         'Mobile developer exploring web technologies',                           'rachelw',     'password123', '2024-03-01', 1, 'author'),
  ('Kevin',   'Harris',   'kevin@example.com',          'Systems administrator and Linux enthusiast',                            'kevinh',      'password123', '2024-03-05', 1, 'author'),
  ('Amy',     'Clark',    'amy@example.com',            'Software tester and quality advocate',                                  'amyc',        'password123', '2024-03-08', 1, 'author'),
  ('Steve',   'Lewis',    'steve@example.com',          'Tech lead with passion for mentoring',                                  'stevel',      'password123', '2024-03-10', 1, 'author'),
  ('Caleb',   'Pittman',  'ambassadoor.dev@gmail.com',  'Full Stack Developer in Training',                                      'Ambassadoor', 'Password',    '2024-03-15', 1, 'admin');

-- Seed DemotionQueue
-- admin_id references the admin being demoted; approver_one_id is the admin who initiated it
-- UNIQUE(action, admin_id) means only one pending action per admin at a time
INSERT INTO DemotionQueue (action, admin_id, approver_one_id)
VALUES
  ('demote', 3, 16);

-- Seed Subscriptions
-- follower_id is the user following, author_id is the user being followed
-- UNIQUE(follower_id, author_id) prevents duplicate subscriptions
INSERT INTO Subscriptions (follower_id, author_id, created_on)
VALUES
  (2,  1,  '2025-01-16'),  -- Jane follows John
  (4,  1,  '2025-01-17'),  -- Alice follows John
  (5,  1,  '2025-01-18'),  -- Charlie follows John
  (6,  1,  '2025-01-19'),  -- Emma follows John
  (1,  2,  '2025-01-21'),  -- John follows Jane
  (4,  2,  '2025-01-22'),  -- Alice follows Jane
  (7,  2,  '2025-01-23'),  -- Michael follows Jane
  (1,  4,  '2025-02-06'),  -- John follows Alice
  (2,  4,  '2025-02-07'),  -- Jane follows Alice
  (1,  5,  '2025-02-09'),  -- John follows Charlie
  (3,  5,  '2025-02-10'),  -- Bob follows Charlie
  (1,  6,  '2025-02-13'),  -- John follows Emma
  (2,  6,  '2025-02-14'),  -- Jane follows Emma
  (8,  6,  '2025-02-15'),  -- Sarah follows Emma
  (4,  7,  '2025-02-15'),  -- Alice follows Michael
  (6,  7,  '2025-02-16'),  -- Emma follows Michael
  (1,  8,  '2025-02-17'),  -- John follows Sarah
  (5,  8,  '2025-02-18'),  -- Charlie follows Sarah
  (2,  9,  '2025-02-19'),  -- Jane follows David
  (7,  9,  '2025-02-20'),  -- Michael follows David
  (2,  10, '2025-02-21'),  -- Jane follows Lisa
  (10, 11, '2025-02-24'),  -- Lisa follows Tom
  (11, 13, '2025-02-26'),  -- Tom follows Kevin
  (12, 13, '2025-02-27'),  -- Rachel follows Kevin
  (5,  14, '2025-02-28'),  -- Charlie follows Amy
  (16, 1,  '2025-03-01'),  -- Caleb follows John
  (16, 14, '2025-03-02'),  -- Caleb follows Amy
  (15, 16, '2025-03-03');  -- Steve follows Caleb

-- Seed Categories
INSERT INTO Categories (label) VALUES
  ('Technology'),
  ('Career'),
  ('Lifestyle'),
  ('Tutorial'),
  ('Opinion'),
  ('News'),
  ('Review'),
  ('Tips & Tricks'),
  ('Fluff'),
  ('Life');

-- Seed Tags
INSERT INTO Tags (label) VALUES
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
INSERT INTO Reactions (label, emoji) VALUES
  ('happy',      '😊'),
  ('pink heart', '🩷'),
  ('laugh',      '😂'),
  ('mind-blown', '🤯'),
  ('fire',       '🔥'),
  ('thumbs-up',  '👍'),
  ('celebrate',  '🎉');

-- Seed Posts
-- (user_id, category_id, title, publication_date, content, status, submitted_at, reviewed_at, reviewer_id)
INSERT INTO Posts (user_id, category_id, title, publication_date, content, status, reviewed_at, reviewer_id)
VALUES
  (1,  1, 'Getting Started with Python',              '2025-01-15', 'Python is a great language for beginners. In this post, we will explore the fundamentals of Python programming including variables, data types, and control structures. Perfect for those starting their coding journey!',                                                                           'approved', '2025-01-15', 1),
  (1,  4, 'My Side Project Journey',                  '2025-01-20', 'Here is how I built my first web app from scratch. It took 3 months of evening work, but the learning experience was invaluable. I will share my tech stack, challenges faced, and lessons learned.',                                                                                              'approved', '2025-01-20', 1),
  (2,  1, 'React Best Practices 2025',                '2025-01-25', 'Learn the best practices for React development in 2025. We will cover component composition, state management, performance optimization, and more.',                                                                                                                                               'approved', '2025-01-25', 1),
  (2,  3, 'Coding Memes That Made Me Laugh',          '2025-02-01', 'Here are my favorite coding memes from last month. Sometimes you need a good laugh during debugging sessions!',                                                                                                                                                                                    'approved', '2025-02-01', 1),
  (4,  1, 'CSS Grid vs Flexbox: When to Use Each',    '2025-02-05', 'Understanding when to use CSS Grid and when to use Flexbox can be confusing. This comprehensive guide will help you choose the right tool for your layout needs.',                                                                                                                                  'approved', '2025-02-05', 1),
  (5,  2, 'Building a CI/CD Pipeline from Scratch',   '2025-02-08', 'Step-by-step guide to setting up a complete CI/CD pipeline using GitHub Actions and Docker. Automate your deployments and improve your development workflow.',                                                                                                                                      'approved', '2025-02-08', 1),
  (1,  1, 'Advanced SQL Queries Explained',           '2025-02-10', 'Master complex SQL queries with these tips and examples. We will cover joins, subqueries, CTEs, and window functions.',                                                                                                                                                                             'approved', '2025-02-10', 1),
  (6,  1, 'Django vs Flask: Which to Choose?',        '2025-02-12', 'A detailed comparison of Django and Flask frameworks. Learn the pros and cons of each to make an informed decision for your next project.',                                                                                                                                                         'approved', '2025-02-12', 1),
  (7,  1, 'API Security Best Practices',              '2025-02-14', 'Secure your APIs with these essential practices. Topics include authentication, authorization, rate limiting, and input validation.',                                                                                                                                                                'approved', '2025-02-14', 1),
  (8,  4, 'How to Write Better Documentation',        '2025-02-16', 'Good documentation is crucial for project success. Here are my tips for writing clear, comprehensive documentation that developers will actually read.',                                                                                                                                             'approved', '2025-02-16', 1),
  (9,  1, 'Introduction to Docker Containers',        '2025-02-18', 'Docker has revolutionized application deployment. This tutorial covers the basics of containerization and how to get started with Docker.',                                                                                                                                                         'approved', '2025-02-18', 1),
  (10, 5, 'The Future of Web Development',            '2025-02-20', 'My thoughts on where web development is heading. From WebAssembly to edge computing, the landscape is constantly evolving.',                                                                                                                                                                        'approved', '2025-02-20', 1),
  (11, 4, 'Building RESTful APIs with Node.js',       '2025-02-22', 'Complete guide to building scalable RESTful APIs using Node.js and Express. Includes code examples and best practices.',                                                                                                                                                                            'approved', '2025-02-22', 1),
  (12, 3, 'My Favorite VS Code Extensions',           '2025-02-23', 'Here are the VS Code extensions I cannot live without. They have boosted my productivity significantly!',                                                                                                                                                                                          'approved', '2025-02-23', 1),
  (13, 8, 'Git Tips Every Developer Should Know',     '2025-02-24', 'Essential Git commands and workflows that will make your life easier. From rebasing to cherry-picking, we cover it all.',                                                                                                                                                                           'approved', '2025-02-24', 1),
  (14, 2, 'Transitioning from Junior to Senior Dev',  '2025-02-24', 'What it takes to grow from junior to senior developer. Technical skills are important, but soft skills matter too.',                                                                                                                                                                               'approved', '2025-02-24', 1),
  (2,  7, 'React Query: A Deep Dive',                 '2025-02-25', 'React Query has changed how I handle server state in React applications. Here is everything you need to know about this powerful library.',                                                                                                                                                         'approved', '2025-02-25', 1),
  (4,  1, 'TypeScript Tips for Beginners',            '2025-02-25', 'TypeScript can seem intimidating at first. These practical tips will help you get comfortable with type safety in your JavaScript projects.',                                                                                                                                                       'approved', '2025-02-25', 1),
  (6,  8, '10 JavaScript Array Methods You Should Know', '2025-03-01', 'JavaScript array methods are powerful tools. Master these 10 methods to write cleaner, more efficient code.',                                                                                                                                                                                  'approved', '2025-03-01', 16),
  (7,  4, 'Building a Todo App with React Hooks',     NULL,         'Complete tutorial on building a todo application using React hooks. Perfect project for learning modern React patterns.',                                                                                                                                                                           'rejected', '2025-03-02', 16),
  (8,  1, 'Understanding Async/Await in JavaScript',  NULL,         'Async/await makes asynchronous code easier to read and write. This guide explains how it works under the hood.',                                                                                                                                                                                   'rejected', '2025-03-03', 16),
  (11, 5, 'Why I Switched to Tailwind CSS',           NULL,         'My experience switching from traditional CSS to Tailwind. The utility-first approach has transformed my development workflow.',                                                                                                                                                                     'submitted', NULL,       NULL),
  (13, 2, 'Negotiating Your First Tech Job Offer',    '2025-03-05', 'Tips for negotiating salary and benefits in the tech industry. Know your worth and do not be afraid to ask for what you deserve.',                                                                                                                                                                 'approved', '2025-03-05', 16),
  (14, 4, 'Introduction to GraphQL',                  '2025-03-06', 'GraphQL is an alternative to REST that gives clients more control. Learn the basics and see if it is right for your project.',                                                                                                                                                                     'approved', '2025-03-06', 16),
  (15, 5, 'Testing an Author''s Permissions',         '2025-03-07', 'A walkthrough of how author permissions work in the app and what actions are restricted.',                                                                                                                                                                                                         'approved', '2025-03-07', 16);

-- Seed Comments
-- (post_id, author_id, subject, content, created_on)
INSERT INTO Comments (post_id, author_id, subject, content, created_on)
VALUES
  (1,  2,  'Excellent Article',        'Great introduction! Very helpful for beginners.',                  '2025-01-16'),
  (1,  4,  'Very Informative',         'Thanks for sharing. I learned a lot from this.',                   '2025-01-17'),
  (1,  6,  'Follow-up Request',        'Could you do a follow-up on advanced Python topics?',              '2025-01-18'),
  (2,  5,  'Motivational',             'Inspiring story! Keep it up.',                                    '2025-01-21'),
  (2,  3,  'Question',                 'What tech stack did you use?',                                    '2025-01-22'),
  (2,  7,  'Related Project',          'I am working on a similar project. This helps!',                  '2025-01-23'),
  (3,  1,  'Helpful Tips',             'These tips are gold. Thank you!',                                 '2025-01-26'),
  (3,  4,  'Constructive Feedback',    'I disagree with point #3, but overall great article.',            '2025-01-27'),
  (3,  8,  'More Please',              'Would love to see more React content from you.',                  '2025-01-28'),
  (4,  1,  'Funny',                    'Haha, the semicolon one got me!',                                 '2025-02-02'),
  (4,  10, 'So True',                  'These are too relatable!',                                        '2025-02-03'),
  (5,  1,  'Perfect Timing',           'Perfect timing! I was just learning about this.',                 '2025-02-06'),
  (5,  6,  'Great Visuals',            'The visual examples really help understand the concepts.',        '2025-02-07'),
  (5,  11, 'Suggestion',               'Can you cover CSS animations next?',                              '2025-02-08'),
  (6,  2,  'Time Saver',               'This saved me so much time setting up my pipeline!',              '2025-02-09'),
  (6,  4,  'Repo Request',             'Do you have a GitHub repo with the complete setup?',              '2025-02-10'),
  (7,  3,  'Game Changer',             'Window functions were a game changer for me.',                    '2025-02-11'),
  (7,  5,  'Practical Examples',       'Great examples! Very practical.',                                 '2025-02-12'),
  (8,  1,  'Flask User',               'I have been using Flask for years. Good comparison!',             '2025-02-13'),
  (8,  2,  'Decision Help',            'This helps me decide for my new project. Thanks!',                '2025-02-14'),
  (9,  4,  'Important Topic',          'Security is often overlooked. Thanks for covering this!',         '2025-02-15'),
  (9,  6,  'OAuth Question',           'What about OAuth2? Can you cover that?',                         '2025-02-16'),
  (9,  12, 'Implementing Now',         'Implementing these in my API right away.',                        '2025-02-17'),
  (10, 1,  'Professional Approval',    'As a documentation writer, I approve this message!',              '2025-02-17'),
  (10, 5,  'Diagrams Help',            'Adding diagrams makes documentation so much better.',             '2025-02-18'),
  (11, 1,  'Workflow Changed',         'Docker changed my development workflow completely.',               '2025-02-19'),
  (11, 3,  'Concept Clicked',          'The container concept clicked after reading this.',               '2025-02-20'),
  (12, 2,  'Thought Provoking',        'Interesting perspective on the future!',                          '2025-02-21'),
  (12, 7,  'WebAssembly Fan',          'I am excited about WebAssembly too!',                             '2025-02-22'),
  (13, 1,  'Love Express',             'Express makes building APIs so straightforward.',                 '2025-02-23'),
  (13, 9,  'Comprehensive',            'Very comprehensive tutorial. Thanks!',                            '2025-02-24'),
  (14, 1,  'Extension Recommendation', 'GitLens extension is a must-have!',                               '2025-02-24'),
  (14, 4,  'Same Here',                'I use all of these! Great list.',                                 '2025-02-25'),
  (15, 2,  'Rebase Power',             'Interactive rebase is so powerful once you learn it.',            '2025-02-25'),
  (15, 11, 'Cleared Confusion',        'This cleared up my confusion about merge vs rebase.',             '2025-02-26'),
  (17, 1,  'Code Simplification',      'React Query has simplified my code so much.',                    '2025-02-26'),
  (17, 3,  'Comparison Question',      'How does it compare to Redux?',                                   '2025-02-27'),
  (18, 2,  'Refactoring Safety',       'TypeScript makes refactoring so much safer.',                    '2025-02-26'),
  (23, 5,  'Helpful Advice',           'Negotiation was scary at first but this advice helped!',          '2025-03-01'),
  (24, 2,  'Looks Complex',            'GraphQL looks interesting but seems complex.',                    '2025-03-02');

-- Seed PostTags
-- Tag IDs: 1=JavaScript, 2=Python, 3=React, 4=Node.js, 5=CSS, 6=HTML, 7=SQL,
--          8=Web Development, 9=Tutorial, 10=Opinion, 11=Django, 12=TypeScript,
--          13=Docker, 14=DevOps, 15=Security, 16=Testing, 17=Performance,
--          18=Design, 19=Career Advice, 20=Productivity
INSERT INTO PostTags (post_id, tag_id)
VALUES
  (1,  2),   -- Getting Started with Python        → Python
  (1,  9),   -- Getting Started with Python        → Tutorial
  (2,  2),   -- My Side Project Journey            → Python
  (2,  8),   -- My Side Project Journey            → Web Development
  (2,  11),  -- My Side Project Journey            → Django
  (3,  3),   -- React Best Practices               → React
  (3,  8),   -- React Best Practices               → Web Development
  (3,  1),   -- React Best Practices               → JavaScript
  (4,  10),  -- Coding Memes                       → Opinion
  (5,  5),   -- CSS Grid vs Flexbox                → CSS
  (5,  6),   -- CSS Grid vs Flexbox                → HTML
  (5,  8),   -- CSS Grid vs Flexbox                → Web Development
  (5,  18),  -- CSS Grid vs Flexbox                → Design
  (6,  4),   -- Building a CI/CD Pipeline          → Node.js
  (6,  13),  -- Building a CI/CD Pipeline          → Docker
  (6,  14),  -- Building a CI/CD Pipeline          → DevOps
  (7,  7),   -- Advanced SQL Queries               → SQL
  (7,  9),   -- Advanced SQL Queries               → Tutorial
  (8,  2),   -- Django vs Flask                    → Python
  (8,  11),  -- Django vs Flask                    → Django
  (9,  15),  -- API Security Best Practices        → Security
  (9,  8),   -- API Security Best Practices        → Web Development
  (10, 8),   -- How to Write Better Documentation  → Web Development
  (10, 19),  -- How to Write Better Documentation  → Career Advice
  (11, 13),  -- Introduction to Docker             → Docker
  (11, 14),  -- Introduction to Docker             → DevOps
  (12, 1),   -- The Future of Web Development      → JavaScript
  (12, 10),  -- The Future of Web Development      → Opinion
  (13, 4),   -- Building RESTful APIs with Node.js → Node.js
  (13, 8),   -- Building RESTful APIs with Node.js → Web Development
  (13, 9),   -- Building RESTful APIs with Node.js → Tutorial
  (14, 18),  -- My Favorite VS Code Extensions     → Design
  (14, 20),  -- My Favorite VS Code Extensions     → Productivity
  (15, 1),   -- Git Tips                           → JavaScript
  (15, 20),  -- Git Tips                           → Productivity
  (16, 19),  -- Transitioning Junior to Senior     → Career Advice
  (17, 3),   -- React Query                        → React
  (17, 1),   -- React Query                        → JavaScript
  (17, 8),   -- React Query                        → Web Development
  (18, 12),  -- TypeScript Tips                    → TypeScript
  (18, 1),   -- TypeScript Tips                    → JavaScript
  (18, 9),   -- TypeScript Tips                    → Tutorial
  (19, 1),   -- 10 JavaScript Array Methods        → JavaScript
  (19, 9),   -- 10 JavaScript Array Methods        → Tutorial
  (20, 3),   -- Building a Todo App                → React
  (20, 9),   -- Building a Todo App                → Tutorial
  (21, 1),   -- Understanding Async/Await          → JavaScript
  (21, 9),   -- Understanding Async/Await          → Tutorial
  (22, 5),   -- Why I Switched to Tailwind         → CSS
  (22, 18),  -- Why I Switched to Tailwind         → Design
  (22, 8),   -- Why I Switched to Tailwind         → Web Development
  (23, 19),  -- Negotiating Your First Tech Job    → Career Advice
  (24, 1),   -- Introduction to GraphQL            → JavaScript
  (24, 8),   -- Introduction to GraphQL            → Web Development
  (25, 16),  -- Testing an Author's Permissions    → Testing
  (25, 9);   -- Testing an Author's Permissions    → Tutorial

-- Seed PostReactions
-- Reaction IDs: 1=happy 😊, 2=pink heart 🩷, 3=laugh 😂, 4=mind-blown 🤯, 5=fire 🔥, 6=thumbs-up 👍, 7=celebrate 🎉
-- UNIQUE(user_id, reaction_id, post_id) — one of each reaction type per user per post
INSERT INTO PostReactions (user_id, reaction_id, post_id)
VALUES
  (2,  1, 1),   -- Jane     → happy     on post 1
  (4,  1, 1),   -- Alice    → happy     on post 1
  (5,  6, 1),   -- Charlie  → thumbs-up on post 1
  (6,  2, 1),   -- Emma     → pink heart on post 1
  (1,  2, 3),   -- John     → pink heart on post 3
  (3,  5, 3),   -- Bob      → fire      on post 3
  (5,  6, 3),   -- Charlie  → thumbs-up on post 3
  (1,  3, 4),   -- John     → laugh     on post 4
  (2,  3, 4),   -- Jane     → laugh     on post 4
  (3,  3, 4),   -- Bob      → laugh     on post 4
  (10, 3, 4),   -- Lisa     → laugh     on post 4
  (1,  5, 5),   -- John     → fire      on post 5
  (2,  5, 5),   -- Jane     → fire      on post 5
  (11, 6, 5),   -- Tom      → thumbs-up on post 5
  (2,  6, 6),   -- Jane     → thumbs-up on post 6
  (4,  2, 6),   -- Alice    → pink heart on post 6
  (9,  5, 6),   -- David    → fire      on post 6
  (3,  6, 7),   -- Bob      → thumbs-up on post 7
  (5,  1, 7),   -- Charlie  → happy     on post 7
  (8,  2, 7),   -- Sarah    → pink heart on post 7
  (1,  6, 8),   -- John     → thumbs-up on post 8
  (2,  1, 8),   -- Jane     → happy     on post 8
  (5,  4, 8),   -- Charlie  → mind-blown on post 8
  (4,  5, 9),   -- Alice    → fire      on post 9
  (6,  2, 9),   -- Emma     → pink heart on post 9
  (12, 6, 9),   -- Rachel   → thumbs-up on post 9
  (1,  6, 10),  -- John     → thumbs-up on post 10
  (5,  2, 10),  -- Charlie  → pink heart on post 10
  (8,  1, 10),  -- Sarah    → happy     on post 10
  (1,  5, 11),  -- John     → fire      on post 11
  (3,  6, 11),  -- Bob      → thumbs-up on post 11
  (7,  4, 11),  -- Michael  → mind-blown on post 11
  (2,  4, 12),  -- Jane     → mind-blown on post 12
  (7,  6, 12),  -- Michael  → thumbs-up on post 12
  (13, 1, 12),  -- Kevin    → happy     on post 12
  (1,  6, 13),  -- John     → thumbs-up on post 13
  (9,  5, 13),  -- David    → fire      on post 13
  (11, 2, 13),  -- Tom      → pink heart on post 13
  (1,  1, 14),  -- John     → happy     on post 14
  (4,  2, 14),  -- Alice    → pink heart on post 14
  (10, 6, 14),  -- Lisa     → thumbs-up on post 14
  (2,  6, 15),  -- Jane     → thumbs-up on post 15
  (11, 1, 15),  -- Tom      → happy     on post 15
  (13, 5, 15),  -- Kevin    → fire      on post 15
  (5,  2, 16),  -- Charlie  → pink heart on post 16
  (8,  6, 16),  -- Sarah    → thumbs-up on post 16
  (14, 1, 16),  -- Amy      → happy     on post 16
  (1,  5, 17),  -- John     → fire      on post 17
  (3,  2, 17),  -- Bob      → pink heart on post 17
  (9,  6, 17),  -- David    → thumbs-up on post 17
  (2,  6, 18),  -- Jane     → thumbs-up on post 18
  (4,  1, 18),  -- Alice    → happy     on post 18
  (7,  2, 18),  -- Michael  → pink heart on post 18
  (1,  2, 23),  -- John     → pink heart on post 23
  (5,  6, 23),  -- Charlie  → thumbs-up on post 23
  (14, 1, 23),  -- Amy      → happy     on post 23
  (2,  4, 24),  -- Jane     → mind-blown on post 24
  (6,  6, 24),  -- Emma     → thumbs-up on post 24
  (9,  1, 24),  -- David    → happy     on post 24
  (16, 7, 25);  -- Caleb    → celebrate on post 25

