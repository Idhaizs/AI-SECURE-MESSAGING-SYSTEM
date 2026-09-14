-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 13, 2026 at 03:55 PM
-- Server version: 8.0.42
-- PHP Version: 8.3.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `secure_messaging`
--

-- --------------------------------------------------------

--
-- Table structure for table `alerts`
--

CREATE TABLE `alerts` (
  `id` int NOT NULL,
  `triggered_by_id` int NOT NULL,
  `message_id` int DEFAULT NULL,
  `file_id` int DEFAULT NULL,
  `alert_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `severity` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `details` text COLLATE utf8mb4_unicode_ci,
  `is_resolved` tinyint(1) DEFAULT NULL,
  `resolved_by_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `alert_id` int DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `threat_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT 'none',
  `alert_detail` text COLLATE utf8mb4_unicode_ci,
  `status` enum('unread','read','resolved') COLLATE utf8mb4_unicode_ci DEFAULT 'unread'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `audit_logs`
--

CREATE TABLE `audit_logs` (
  `log_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `action` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ip_address` varchar(45) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `detail` text COLLATE utf8mb4_unicode_ci,
  `timestamp` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `audit_logs`
--

INSERT INTO `audit_logs` (`log_id`, `user_id`, `action`, `ip_address`, `detail`, `timestamp`) VALUES
(1, 7, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-07-23 15:38:05'),
(2, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-07-24 10:13:52'),
(3, 4, 'SEND_MESSAGE', '127.0.0.1', 'To user: 8', '2026-07-24 10:42:20'),
(4, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-07-24 11:52:48'),
(5, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-07-24 12:03:23'),
(6, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-07-24 12:04:00'),
(7, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-07-24 12:05:43'),
(8, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-04 22:15:16'),
(9, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 00:02:18'),
(10, 5, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 00:03:25'),
(11, 5, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 00:05:01'),
(12, 6, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 00:05:45'),
(13, 6, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 00:06:03'),
(14, 7, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 00:06:40'),
(15, 7, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 00:06:58'),
(16, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 00:07:29'),
(17, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 00:09:06'),
(18, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-05 00:09:29'),
(19, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-05 00:09:50'),
(20, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-05 00:10:08'),
(21, NULL, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 13:18:09'),
(22, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 13:26:44'),
(23, 4, 'SEND_MESSAGE', '127.0.0.1', 'To user: 8', '2026-08-05 13:26:57'),
(24, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-05 13:27:37'),
(25, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-05 13:44:53'),
(26, 8, 'SEND_MESSAGE', '127.0.0.1', 'To user: 4', '2026-08-05 13:45:02'),
(27, NULL, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-06 15:38:50'),
(28, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-06 15:39:35'),
(29, 4, 'CREATE_GROUP', '127.0.0.1', 'Group ID: 2', '2026-08-06 15:53:22'),
(30, 4, 'ADD_GROUP_MEMBER', '127.0.0.1', 'Group ID: 2, User ID: 8', '2026-08-06 16:14:19'),
(31, 4, 'UPDATE_GROUP', '127.0.0.1', 'Group ID: 2', '2026-08-06 16:15:29'),
(32, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-06 16:35:59'),
(33, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-13 11:01:16'),
(34, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-13 11:02:50'),
(35, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-13 11:03:04'),
(36, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-13 11:03:28'),
(37, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-13 11:03:44'),
(38, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-13 11:04:36'),
(39, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-13 11:07:18'),
(40, 1, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: admin', '2026-08-24 16:15:47'),
(41, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-24 16:16:24'),
(42, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-24 16:37:36'),
(43, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-24 16:37:58'),
(44, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-24 16:39:13'),
(45, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-27 00:00:48'),
(46, 4, 'UPLOAD_FILE', '127.0.0.1', 'File: AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf, Protected: False, Scan: clean', '2026-08-27 00:11:32'),
(47, 4, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 1 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:11:40'),
(48, 4, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 1 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:13:41'),
(49, 4, 'DELETE_MESSAGE', '127.0.0.1', 'Message ID: 7', '2026-08-27 00:13:59'),
(50, 4, 'UPLOAD_FILE', '127.0.0.1', 'File: AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf, Protected: False, Scan: clean', '2026-08-27 00:14:27'),
(51, 4, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 2 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:14:30'),
(52, 4, 'UPLOAD_FILE', '127.0.0.1', 'File: AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf, Protected: True, Scan: clean', '2026-08-27 00:18:32'),
(53, 4, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 3 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:18:41'),
(54, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 00:19:52'),
(55, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-27 00:21:01'),
(56, 8, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 9 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:32:28'),
(57, 8, 'FILE_DOWNLOAD_FAILED_PASSWORD', '127.0.0.1', 'Failed password attempt for File ID: 9 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 00:33:02'),
(58, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 00:38:56'),
(59, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-27 00:39:36'),
(60, NULL, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 10:12:02'),
(61, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-27 10:35:49'),
(62, 4, 'UPLOAD_FILE', '127.0.0.1', 'File: AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf, Protected: True, Scan: clean', '2026-08-27 10:38:07'),
(63, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 10:42:23'),
(64, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-27 10:43:08'),
(65, 8, 'FILE_DOWNLOAD_SUCCESS', '127.0.0.1', 'File ID: 10 (AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf)', '2026-08-27 10:43:39'),
(66, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 10:46:43'),
(67, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-27 10:47:47'),
(68, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-27 11:19:19'),
(69, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-27 13:07:15'),
(70, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-28 11:01:29'),
(71, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-28 11:21:13'),
(72, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-28 11:21:33'),
(73, 8, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: daniel.lim', '2026-08-28 11:23:07'),
(74, 8, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: daniel.lim', '2026-08-28 11:23:16'),
(75, 4, 'CREATE_MEETING', '127.0.0.1', 'Meeting ID: 1, Title: FYP Final Project Discussion', '2026-08-28 11:24:30'),
(76, 4, 'DELETE_MEETING', '127.0.0.1', 'Meeting ID: 1', '2026-08-28 11:26:54'),
(77, 4, 'CREATE_MEETING', '127.0.0.1', 'Meeting ID: 2, Title: FYP Discusiion', '2026-08-28 11:36:14'),
(78, 4, 'CREATE_MEETING', '127.0.0.1', 'Meeting ID: 3, Title: Presentation FYP', '2026-08-28 11:50:07'),
(79, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-28 12:14:09'),
(80, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-08-28 12:14:46'),
(81, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-28 12:15:12'),
(82, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-08-28 12:15:42'),
(83, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-08-28 12:17:37'),
(84, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-02 22:58:08'),
(85, 4, 'SEND_MESSAGE', '127.0.0.1', 'To user: 8', '2026-09-02 23:21:34'),
(86, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-02 23:21:52'),
(87, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-02 23:22:36'),
(88, 8, 'SEND_MESSAGE', '127.0.0.1', 'To user: 4', '2026-09-02 23:22:57'),
(89, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-02 23:23:48'),
(90, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-02 23:24:09'),
(91, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-02 23:57:09'),
(92, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-03 08:42:08'),
(93, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-03 08:44:51'),
(94, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-03 08:45:11'),
(95, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-03 08:47:25'),
(96, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:16:39'),
(97, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:17:47'),
(98, 8, 'SEND_MESSAGE', '127.0.0.1', 'To user: 4', '2026-09-04 00:18:22'),
(99, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-04 00:27:17'),
(100, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:27:53'),
(101, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-04 00:28:42'),
(102, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:30:36'),
(103, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:31:19'),
(104, 4, 'SEND_MESSAGE', '127.0.0.1', 'To user: 8', '2026-09-04 00:31:43'),
(105, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-04 00:40:14'),
(106, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-04 00:41:18'),
(107, 8, 'SEND_MESSAGE', '127.0.0.1', 'To user: 4', '2026-09-04 00:42:55'),
(108, 4, 'SEND_MESSAGE', '127.0.0.1', 'To user: 8', '2026-09-04 00:43:07'),
(109, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-04 00:45:05'),
(110, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-04 00:45:18'),
(111, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-09 14:54:13'),
(112, 8, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-09 14:59:12'),
(113, 8, 'CREATE_MEETING', '127.0.0.1', 'Meeting ID: 4, Title: Group Project', '2026-09-09 15:02:13'),
(114, 8, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-09 15:16:22'),
(115, 7, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-09 15:17:16'),
(116, 7, 'CREATE_MEETING', '127.0.0.1', 'Meeting ID: 5, Title: Meeting for Event Setup', '2026-09-09 15:18:53'),
(117, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-09 15:43:21'),
(118, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-12 10:25:05'),
(119, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-12 10:26:10'),
(120, 9, 'REGISTER', '127.0.0.1', 'New user registered (Pending Admin Approval)', '2026-09-12 10:37:41'),
(121, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-12 10:39:54'),
(122, 9, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-12 11:13:57'),
(123, 9, 'UPDATE_USERNAME', '127.0.0.1', 'Updated username to Azlan Kasim', '2026-09-12 11:14:48'),
(124, 9, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-12 11:40:18'),
(125, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-12 11:56:26'),
(126, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-12 22:02:01'),
(127, NULL, 'FAILED_LOGIN', '127.0.0.1', 'Failed login attempt for: Zaini', '2026-09-12 22:20:07'),
(128, 4, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-12 22:21:03'),
(129, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-12 23:44:34'),
(130, 4, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-12 23:44:43'),
(131, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-13 12:26:58'),
(132, 1, 'ADMIN_LOGIN', '127.0.0.1', 'Admin logged in', '2026-09-13 22:44:55'),
(133, 1, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-13 22:45:42'),
(134, 9, 'LOGIN', '127.0.0.1', 'User logged in', '2026-09-13 22:46:47'),
(135, 9, 'LOGOUT', '127.0.0.1', 'User logged out', '2026-09-13 23:48:57');

-- --------------------------------------------------------

--
-- Table structure for table `files`
--

CREATE TABLE `files` (
  `id` int NOT NULL,
  `uploader_id` int NOT NULL,
  `receiver_id` int DEFAULT NULL,
  `original_filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `stored_filename` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `file_type` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `file_size` bigint DEFAULT NULL,
  `encrypted_key` blob NOT NULL,
  `iv` blob NOT NULL,
  `is_suspicious` tinyint(1) DEFAULT NULL,
  `virustotal_result` text COLLATE utf8mb4_unicode_ci,
  `is_executable_blocked` tinyint(1) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `file_id` int DEFAULT NULL,
  `file_name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` int DEFAULT NULL,
  `message_id` int DEFAULT NULL,
  `file_hash` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `file_path` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT '',
  `is_scanned` tinyint(1) DEFAULT '0',
  `scan_result` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT 'clean',
  `is_password_protected` tinyint(1) DEFAULT '0',
  `file_password_hash` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `files`
--

INSERT INTO `files` (`id`, `uploader_id`, `receiver_id`, `original_filename`, `stored_filename`, `file_type`, `file_size`, `encrypted_key`, `iv`, `is_suspicious`, `virustotal_result`, `is_executable_blocked`, `created_at`, `file_id`, `file_name`, `user_id`, `message_id`, `file_hash`, `file_path`, `is_scanned`, `scan_result`, `is_password_protected`, `file_password_hash`) VALUES
(1, 4, 8, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', NULL, NULL, '', '', NULL, NULL, NULL, NULL, NULL, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 4, 7, 'aa69cb3b62933927efd28dbbfe6cf9c0865794050ad24857d332cdcea62e03b3', 'app/static/uploads\\4\\AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 1, 'clean', 0, NULL),
(2, 4, 8, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', NULL, NULL, '', '', NULL, NULL, NULL, NULL, NULL, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 4, 8, 'aa69cb3b62933927efd28dbbfe6cf9c0865794050ad24857d332cdcea62e03b3', 'app/static/uploads\\4\\AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 1, 'clean', 0, NULL),
(3, 4, 8, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', NULL, NULL, '', '', NULL, NULL, NULL, NULL, NULL, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 4, 9, 'aa69cb3b62933927efd28dbbfe6cf9c0865794050ad24857d332cdcea62e03b3', 'app/static/uploads\\4\\AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 1, 'clean', 1, 'scrypt:32768:8:1$6No3qmF6xkZ16dUJ$8c0013a557bb2e6e483908d83fbe957e43e320ce22bdbdadc6aa8061fd455bfbe45d01ed4bd3cede7144e9b1caf2290e9b4d572ff3c4bcbf14b8cdabb6724594'),
(4, 4, 8, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', NULL, NULL, '', '', NULL, NULL, NULL, NULL, NULL, 'AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 4, 10, 'aa69cb3b62933927efd28dbbfe6cf9c0865794050ad24857d332cdcea62e03b3', 'app/static/uploads\\4\\AM2412018299_-_TUGASAN_KELAS_PENULISAN_REFLEKTIF_-_MPU3192_SEC_03.pdf', 1, 'clean', 1, 'scrypt:32768:8:1$pjfcqJqqu0crv8Yx$90445188acab531e345476e77546600ce40dd051c5383909bc5ef9fe0e93e8f04b2f0379bf7af95afb827a4c0de3309689e8ef1ad44581bc103fb4f3365b0437');

-- --------------------------------------------------------

--
-- Table structure for table `groups`
--

CREATE TABLE `groups` (
  `id` int NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_by_id` int NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `groups`
--

INSERT INTO `groups` (`id`, `name`, `description`, `created_by_id`, `created_at`) VALUES
(2, 'Project FYP2', 'Welcome to the group everyone!!!', 4, '2026-08-06 15:53:22');

-- --------------------------------------------------------

--
-- Table structure for table `group_members`
--

CREATE TABLE `group_members` (
  `id` int NOT NULL,
  `group_id` int NOT NULL,
  `user_id` int NOT NULL,
  `joined_at` datetime DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT 'member'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `group_members`
--

INSERT INTO `group_members` (`id`, `group_id`, `user_id`, `joined_at`, `role`) VALUES
(2, 2, 4, '2026-08-06 15:53:22', 'member'),
(3, 2, 5, '2026-08-06 15:53:22', 'member'),
(4, 2, 6, '2026-08-06 15:53:22', 'member'),
(5, 2, 7, '2026-08-06 15:53:22', 'member'),
(6, 2, 8, '2026-08-06 16:14:19', 'member');

-- --------------------------------------------------------

--
-- Table structure for table `group_messages`
--

CREATE TABLE `group_messages` (
  `id` int NOT NULL,
  `group_id` int NOT NULL,
  `sender_id` int NOT NULL,
  `encrypted_content` blob NOT NULL,
  `iv` blob NOT NULL,
  `is_flagged` tinyint(1) DEFAULT NULL,
  `is_blocked_msg` tinyint(1) DEFAULT NULL,
  `threat_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `threat_score` float DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `meetings`
--

CREATE TABLE `meetings` (
  `meeting_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `organizer_id` int NOT NULL,
  `meeting_type` varchar(50) NOT NULL DEFAULT 'google_meet',
  `meeting_link_or_location` text,
  `start_time` datetime NOT NULL,
  `end_time` datetime NOT NULL,
  `description` text,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `meetings`
--

INSERT INTO `meetings` (`meeting_id`, `title`, `organizer_id`, `meeting_type`, `meeting_link_or_location`, `start_time`, `end_time`, `description`, `created_at`) VALUES
(2, 'FYP Discusiion', 4, 'google_meet', 'https://meet.google.com/ora-xumi-ccw', '2026-08-28 11:35:00', '2026-08-28 12:35:00', '', '2026-08-28 11:36:14'),
(3, 'Presentation FYP', 4, 'physical', 'UPTM', '2026-09-01 10:00:00', '2026-09-01 12:00:00', '', '2026-08-28 11:50:07'),
(4, 'Group Project', 8, 'google_meet', 'https://meet.google.com/wgy-dgka-bim', '2026-09-10 14:59:00', '2026-09-10 15:59:00', '', '2026-09-09 15:02:12'),
(5, 'Meeting for Event Setup', 7, 'google_meet', 'https://meet.google.com/zfm-miix-aww', '2026-09-11 15:17:00', '2026-09-11 16:17:00', '', '2026-09-09 15:18:53');

-- --------------------------------------------------------

--
-- Table structure for table `meeting_participants`
--

CREATE TABLE `meeting_participants` (
  `id` int NOT NULL,
  `meeting_id` int NOT NULL,
  `user_id` int NOT NULL,
  `status` varchar(20) DEFAULT 'invited',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `meeting_participants`
--

INSERT INTO `meeting_participants` (`id`, `meeting_id`, `user_id`, `status`, `created_at`) VALUES
(2, 2, 4, 'accepted', '2026-08-28 11:36:14'),
(3, 2, 5, 'invited', '2026-08-28 11:36:14'),
(4, 2, 6, 'invited', '2026-08-28 11:36:14'),
(5, 3, 4, 'accepted', '2026-08-28 11:50:07'),
(6, 3, 5, 'invited', '2026-08-28 11:50:07'),
(7, 3, 6, 'invited', '2026-08-28 11:50:07'),
(8, 3, 7, 'invited', '2026-08-28 11:50:07'),
(9, 3, 8, 'invited', '2026-08-28 11:50:07'),
(10, 4, 8, 'accepted', '2026-09-09 15:02:13'),
(11, 4, 4, 'invited', '2026-09-09 15:02:13'),
(12, 5, 7, 'accepted', '2026-09-09 15:18:53'),
(13, 5, 4, 'invited', '2026-09-09 15:18:53'),
(14, 5, 8, 'invited', '2026-09-09 15:18:53');

-- --------------------------------------------------------

--
-- Table structure for table `messages`
--

CREATE TABLE `messages` (
  `id` int NOT NULL,
  `sender_id` int NOT NULL,
  `receiver_id` int NOT NULL,
  `file_id` int DEFAULT NULL,
  `encrypted_content` blob NOT NULL,
  `iv` blob,
  `is_flagged` tinyint(1) DEFAULT NULL,
  `is_blocked_msg` tinyint(1) DEFAULT NULL,
  `threat_type` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `threat_score` float DEFAULT NULL,
  `threat_details` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime DEFAULT NULL,
  `is_deleted` tinyint(1) DEFAULT '0',
  `deleted_at` datetime DEFAULT NULL,
  `message_id` int DEFAULT NULL,
  `sent_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `message_type` enum('text','file') COLLATE utf8mb4_unicode_ci DEFAULT 'text',
  `is_pinned` tinyint(1) DEFAULT '0',
  `is_read` tinyint(1) DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `messages`
--

INSERT INTO `messages` (`id`, `sender_id`, `receiver_id`, `file_id`, `encrypted_content`, `iv`, `is_flagged`, `is_blocked_msg`, `threat_type`, `threat_score`, `threat_details`, `created_at`, `is_deleted`, `deleted_at`, `message_id`, `sent_at`, `message_type`, `is_pinned`, `is_read`) VALUES
(4, 4, 8, NULL, 0x5a30464251554642516e465a6445564e4e485a315932397955556f7a4e315a76553078464d31426e646d67785a3138345a3142565a55356f546d6c4d56454e75634856496245465653553550636d644e5544647a4d465a364e6a645465565a72624451314d453935637a5268535739455130397164585a4d4c554d7462466f796156453950513d3d, '', 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, NULL, '2026-07-24 10:42:20', 'text', 0, 1),
(5, 4, 8, NULL, 0x5a30464251554642516e466a6332316e53484e5864545254656b4e79536d644b5545566e637a4e36567a6374626a42784e586f3163555a6f523352314f55524c64306444545868714e47314a617a4d795a6b6c4c626b527055316c7a64485a4c6445705065554a56523368356253314558315a616345784a61584a304e6b6851536d633950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 5, '2026-08-05 13:26:57', 'text', 0, 1),
(6, 8, 4, NULL, 0x5a30464251554642516e466a637a4e6c63303435596d68736456564a5a453032546a465463574a44616d68574c554659575574486269317a5a454a5162556c6d4f576c6d625870526557396a5631564b63564659546d4e55596a644f643364464e475261596d4e575544553463315a3464324a6e5246387454466c5851334a55636b453950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 6, '2026-08-05 13:45:02', 'text', 0, 1),
(7, 4, 8, NULL, 0x5a30464251554642516e467165454577555468556547394a526b3131656b357551315a484f47564d516b6b3059564279543235684d6d5276536c706a5a316332656b3874626c5a79576b4a6b5a6b4a35546d6c4a566e4a4f4f46464254554e364e6a4e5353486c4f646d3147546d35474d6a68455a546c445831564a4d327068516b464464476845637a56315a44423555303547516b5a6a566d78735a3156465a444a725530354b643046705a335649646e6c32646e5a6f4f55746f6447564356445650656c4e6a5230307955454d304f4556364d4764574f445247624556765a484e55576d4a6852475647616e4a7654576c345746517463305256516c4e4a6254686859306f796557527463316734, NULL, 0, NULL, 'none', NULL, NULL, NULL, 1, NULL, 7, '2026-08-27 00:11:32', 'file', 0, 1),
(8, 4, 8, NULL, 0x5a30464251554642516e4671654552715a47647056334131557a4a3154326c58645456746447706b5a31426f4d556f7a61304a4456544a6d53574a6b64314e6d546c5a61616a526d543359304e5735754f57355753566c426454425a556e643155565674654768356344645862474659516b68734c564a36546d7874596b526951314630554663784e544e565332706a624655784f566c4c4e4530334e6d7845576e6c30544574334e4555795a5464745a4734775245687554325a51555774715232464f596d566956305635616e6f325a55394a4c564e72516b784a5348646f5330647053336c4c626e4248616c646e54486876543267334d48424d62465a435743316a4d316c334c5552486454524d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 8, '2026-08-27 00:14:27', 'file', 0, 1),
(9, 4, 8, NULL, 0x5a30464251554642516e46716545685a5a46565a626a4250636a59335a5531504d6d4d7a62575a30614331455432743364455a514e6e5a5362486c77566b644f513156746133564453323032536a6c34516b566d596b467261465a754d465245646e46786357354451566c59656a6456544842355a327446656d4e336454526664566c45646e4e5964573832516c4a5056306c715630685154335a78647a4e44563070594e3046564e566b7453544a73526c673064477069566c684554474e6c4d4664484d327457655849356558465855325677536e4a786130356b4d6e5671634467314e3252506157703257455a58646d4e5256474a72576d46584f5668465744567355444e4c52464a4d4e457053, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 9, '2026-08-27 00:18:32', 'file', 0, 1),
(10, 4, 8, NULL, 0x5a30464251554642516e46714e6b31514d7931544e464e48656a4e79595652775358567759325649566d396a5355566165484a6153574e7653584e704d6c705a5a56465058326b3353585250537a52556132704b4d6a46664d474e6a535774325647747059586f78563252525630497457584a784e6b747352476f334d336c75626e68704e4735514e4535695547564f64486f34646e5a56646a4977656a6873597a6c4b6232707864456878635670364f544e76626d51354d43316b5a5774565a30707a5833413456454a52536c705257445653636d5534536d4a72627a6c6f5679314e513046585a6c6c79563231495a32315651334a79616a553455466774613146485a324e7455574a5463336450, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 10, '2026-08-27 10:38:07', 'file', 0, 1),
(11, 4, 8, NULL, 0x5a30464251554642516e467452446374616d687255335661646d63746544686b51584650656a424d5a464977625552485a484e724e315a475a336868524868356544465861564974516b56616255777a4e6d6876646c52304d305647626a6c335332314d5830644261303174556a6c54646e704c55544e464f57317256573879546b453950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 11, '2026-09-02 23:21:34', 'text', 0, 1),
(12, 8, 4, NULL, 0x5a30464251554642516e467452446c53656b7774526a4a74555846324e47564b61584578646e5631565545744e6e705462576c3564544a43546e4a70643056575631683153544e4b4e306449656e63354e6d6866526e64575a5664305655706b614731785a566f325445786e53465674556b78455158424d5a7a523456586c455832633950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 12, '2026-09-02 23:22:57', 'text', 0, 1),
(13, 8, 4, NULL, 0x5a30464251554642516e4674576a4e5056445a494c5764365633707261307834533168614d325655545464546255783454554a4261314a475a6d78506544426a4d6d464a61486856557a527963544669546c67316154463664473151626c687a536a4a595445356a56556f334e474674596b646c52444e7956484a5a547a4a4f6448633950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 13, '2026-09-04 00:18:22', 'text', 0, 1),
(14, 4, 8, NULL, 0x5a30464251554642516e4674595552325a6d70494e6d4a5654557871637a4a305358566f61577036566c4a4c4f455646556e564457586c4d5433566664576c704c56465952584a7a623278345156684e5a6a6443526d5243616b356f526d5248636d6444536e6b3061574a4261465271646a5a75595663775748524853574a316333633950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 14, '2026-09-04 00:31:43', 'text', 0, 1),
(15, 8, 4, NULL, 0x5a30464251554642516e4674595539514d4670735353315456466c4f62484a54537a5a43516d524a555735464f46524c596e686b5558687a65565a32533138354d6b70615248413154433035633156754e464e666330786f62324a556430637a5445643162446c55564842435531383162565134636c5a4856445274533068326131453950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 15, '2026-09-04 00:42:55', 'text', 0, 1),
(16, 4, 8, NULL, 0x5a30464251554642516e46745955396865457033656c6c35646e51784e3245314e6e465454314a715a6a6c714f44426c56693035645555355233685061544666516d637964554e5463305647525574424e544e764d475a324c5856766131524d575538356155684464305276536d64544d5535555746464b636a5232636b706a5232633950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 16, '2026-09-04 00:43:06', 'text', 0, 1),
(17, 7, 4, NULL, 0x5a30464251554642516e46765557686b5a6b646e63486c44576b6c336454646a52574a4462555a6c5357396c62475654565639616431497a4f474a5a57464d784e4556304f54466f596b647853455130534852455632356a624652576369317061476c78626c6473575578795a6d464d59325646596a5a5455307854616b705763544d3256545a35596d31495a5868474d453150656d49335932677a56486374527a5a446345564c56564249517a6b7a553068785a476848526d744864326446626c6466515638356248526e6555743165453930523268494c55747a6455317a64303146556c51786331425255446c7a5456704562573533615539304e58706b625746485656706c5a48525563315676556c55345133526b4e6d6b32543052734d6b64774f476c535255354b64455a505355383465484d304e575a46646b524d576e423165586c506455643657456b785646417a4d586f34646b526a5a303034546a4e35546c424262555248516e686d5a573933596b3966635842694e7a41345446453950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 17, '2026-09-09 15:18:53', 'text', 0, 1),
(18, 7, 8, NULL, 0x5a30464251554642516e46765557686b5a6b646e63486c44576b6c336454646a52574a4462555a6c5357396c62475654565639616431497a4f474a5a57464d784e4556304f54466f596b647853455130534852455632356a624652576369317061476c78626c6473575578795a6d464d59325646596a5a5455307854616b705763544d3256545a35596d31495a5868474d453150656d49335932677a56486374527a5a446345564c56564249517a6b7a553068785a476848526d744864326446626c6466515638356248526e6555743165453930523268494c55747a6455317a64303146556c51786331425255446c7a5456704562573533615539304e58706b625746485656706c5a48525563315676556c55345133526b4e6d6b32543052734d6b64774f476c535255354b64455a505355383465484d304e575a46646b524d576e423165586c506455643657456b785646417a4d586f34646b526a5a303034546a4e35546c424262555248516e686d5a573933596b3966635842694e7a41345446453950513d3d, NULL, 0, NULL, 'none', NULL, NULL, NULL, 0, NULL, 18, '2026-09-09 15:18:53', 'text', 0, 0);

-- --------------------------------------------------------

--
-- Table structure for table `message_reads`
--

CREATE TABLE `message_reads` (
  `id` int NOT NULL,
  `message_id` int NOT NULL,
  `reader_id` int NOT NULL,
  `read_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `pinned_messages`
--

CREATE TABLE `pinned_messages` (
  `id` int NOT NULL,
  `group_id` int NOT NULL,
  `group_message_id` int NOT NULL,
  `pinned_by_id` int NOT NULL,
  `duration_hours` int NOT NULL,
  `expires_at` datetime NOT NULL,
  `pinned_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `security_questions`
--

CREATE TABLE `security_questions` (
  `question_id` int NOT NULL,
  `user_id` int NOT NULL,
  `question` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `answer_hash` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `security_questions`
--

INSERT INTO `security_questions` (`question_id`, `user_id`, `question`, `answer_hash`, `created_at`) VALUES
(1, 1, 'What is your secret code?', '555559cb113eeec48bff0c391d8bd4d7aae11452511ac5b54b6b9c44fb4d93be', '2026-07-23 15:35:04'),
(2, 6, 'What city were you born in?', 'a44c37dbd45f25bf7716c4e2dcb9655f53b84957f3a70a58169884b32d1fffa4', '2026-07-23 15:35:04'),
(3, 8, 'What is your childhood nickname?', '5f4e19a4927f8389f295cb20f194514d9f5c121221d2332b59db93a97864d0e3', '2026-07-23 15:35:04'),
(4, 7, 'What was the name of your first pet?', '01892128b95b5c8eccf36e773f4040d78481dccbd06cabb9f514d347a433c520', '2026-07-23 15:35:05'),
(5, 5, 'What is your favourite movie?', '1532e76dbe9d43d0dea98c331ca5ae8a65c5e8e8b99d3e2a42ae989356f6242a', '2026-07-23 15:35:05'),
(6, 4, 'What is your favourite movie?', 'c9344c5f1079f7ce9b007e604829f7e8e4516e9132e098ebd58e2cc7f2a5fd4c', '2026-07-23 15:35:06'),
(7, 9, 'What is your favourite movie?', 'c9344c5f1079f7ce9b007e604829f7e8e4516e9132e098ebd58e2cc7f2a5fd4c', '2026-09-12 10:37:41');

-- --------------------------------------------------------

--
-- Table structure for table `system_settings`
--

CREATE TABLE `system_settings` (
  `setting_id` int NOT NULL,
  `setting_key` varchar(100) NOT NULL,
  `setting_value` text,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data for table `system_settings`
--

INSERT INTO `system_settings` (`setting_id`, `setting_key`, `setting_value`, `updated_at`) VALUES
(1, 'auto_block_threats', 'true', '2026-08-13 11:09:05'),
(2, 'virus_scan_uploads', 'true', '2026-08-13 11:09:05'),
(3, 'ai_threat_detection', 'true', '2026-08-13 11:09:05'),
(4, 'max_file_size_mb', '10', '2026-08-13 11:09:05');

-- --------------------------------------------------------

--
-- Table structure for table `temp_tokens`
--

CREATE TABLE `temp_tokens` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `token_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `expires_at` datetime NOT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `temp_tokens`
--

INSERT INTO `temp_tokens` (`id`, `user_id`, `token_hash`, `expires_at`, `created_at`) VALUES
(1, 1, '$2b$12$3CnvPKgB8mNOLIOWBR.TZutQw3J8jVIHXQbNRpLxaIazzPiPEJfMG', '2026-07-21 09:09:24', '2026-07-21 08:59:24');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `user_id_str` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `full_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `security_question` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `security_answer_hash` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `admin_verify_code_hash` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_blocked` tinyint(1) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  `language_pref` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `user_id` int DEFAULT NULL,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` enum('pending','active','blocked','rejected') COLLATE utf8mb4_unicode_ci DEFAULT 'pending',
  `last_login` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `user_id_str`, `full_name`, `password_hash`, `role`, `security_question`, `security_answer_hash`, `admin_verify_code_hash`, `is_blocked`, `is_active`, `language_pref`, `created_at`, `user_id`, `username`, `email`, `status`, `last_login`) VALUES
(1, 'admin', 'System Administrator', '$2b$12$u93ecmYHBIOj145QmmTmHOQBtiuw/3BZjZJLd6FMj6/h/B5fUlHA2', 'admin', 'Admin code', '$2b$12$pi9C1392ngAkasPBIGW2GeYa3e0EKxqKtHWUPO6Hua1Q9OAw.O7m.', '$2b$12$pi9C1392ngAkasPBIGW2GeYa3e0EKxqKtHWUPO6Hua1Q9OAw.O7m.', 0, 1, 'en', '2026-07-21 08:50:21', 1, 'admin', 'admin@aisecuremsg.com', 'active', '2026-09-13 22:44:55'),
(4, 'SFC-1004', 'Soparjo Bin Ahmad', '$2b$12$N5W2gO2h9X4o5h6lsr9myOTkmN5L7gLbLAt5LC5x0w25V.ny3r846', 'user', 'What is your favourite movie?', '$2b$12$J/TNGZVULNejBCLli/vuQuxB5Y7C.dl8oQeU6.zRT44jNQnzN87LO', NULL, 0, 1, 'en', '2026-07-21 15:02:48', 4, 'Soparjo', 'Soparjo@example.com', 'active', '2026-09-12 22:21:03'),
(5, 'SFC-1005', 'Sarah Hassan', '$2b$12$ACj.A2YKjfYEnjUNhrAOSedk3fsLZRi8wSo0BC2QTKcE3axCuaYz.', 'user', 'What is your favourite movie?', '$2b$12$AmjmlDAfzD4.qy0Lizc6KeCBB1ekPizdmFJBYqrggMfvh4OHwAUZS', NULL, 0, 1, 'en', '2026-07-22 12:46:30', 5, 'sarah.hassan', 'sarah.hassan@example.com', 'active', '2026-08-05 00:03:25'),
(6, 'SFC-1006', 'Amir Zulkifli', '$2b$12$tfaRth1iEPYfZkqSETRLfO75tNP.W2teF5EyYyBfziymmZ3RY7w8m', 'user', 'What city were you born in?', '$2b$12$Ta8iB3u1qU8Fxg/VjvZanOjjQzzXBT55JeOo7UV01Fd434t/7qipK', NULL, 0, 1, 'en', '2026-07-22 12:46:32', 6, 'amir.zulkifli', 'amir.zulkifli@example.com', 'active', '2026-08-05 00:05:45'),
(7, 'SFC-1007', 'Nurul Aina Binti Razak', '$2b$12$4D5db95BQJ3RipWMK38JHe4xMtON/Tkt9F2fBXxVwuFHokkzKsRLq', 'user', 'What was the name of your first pet?', '$2b$12$1ZJ.UhwlKBI/0zRiAUkCuuVQnMDWZbPUxXnWi0YgXf9/UAW1UeJiq', NULL, 0, 1, 'en', '2026-07-22 12:46:33', 7, 'nurul.aina', 'nurul.aina@example.com', 'active', '2026-09-09 15:17:16'),
(8, 'SFC-1008', 'Daniel Lim Wei Jie', '$2b$12$04GMWVIjMFtAkjWwRHnVfuJNgEB.z4MzDa6Wzg0Dwr/l6jrSojFEi', 'user', 'What is your childhood nickname?', '$2b$12$ed8kwIVdvV6C331wTPhTI.r9snMCFuHQV5AVpmq.SqBDbunH4zeiu', NULL, 0, 1, 'en', '2026-07-22 12:46:33', 8, 'daniel.lim', 'daniel.lim@example.com', 'active', '2026-09-09 14:59:12'),
(9, 'SFC-1009', 'Azlan bin Kasim', '$2b$12$h29Fy5WFe7VYhXsO5MU.G.zrrojNeKglSXzTurPpLlp3t6VXrir1a', 'user', 'What is your favourite movie?', 'c9344c5f1079f7ce9b007e604829f7e8e4516e9132e098ebd58e2cc7f2a5fd4c', NULL, 0, 1, 'en', '2026-09-12 11:18:00', 9, 'Azlan Kasim', 'muhammadidham168@gmail.com', 'active', '2026-09-13 22:46:47');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `alerts`
--
ALTER TABLE `alerts`
  ADD PRIMARY KEY (`id`),
  ADD KEY `triggered_by_id` (`triggered_by_id`),
  ADD KEY `message_id` (`message_id`),
  ADD KEY `file_id` (`file_id`),
  ADD KEY `resolved_by_id` (`resolved_by_id`),
  ADD KEY `ix_alerts_created_at` (`created_at`);

--
-- Indexes for table `audit_logs`
--
ALTER TABLE `audit_logs`
  ADD PRIMARY KEY (`log_id`);

--
-- Indexes for table `files`
--
ALTER TABLE `files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `uploader_id` (`uploader_id`),
  ADD KEY `receiver_id` (`receiver_id`);

--
-- Indexes for table `groups`
--
ALTER TABLE `groups`
  ADD PRIMARY KEY (`id`),
  ADD KEY `created_by_id` (`created_by_id`);

--
-- Indexes for table `group_members`
--
ALTER TABLE `group_members`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `group_id` (`group_id`,`user_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `group_messages`
--
ALTER TABLE `group_messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `group_id` (`group_id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `ix_group_messages_created_at` (`created_at`);

--
-- Indexes for table `meetings`
--
ALTER TABLE `meetings`
  ADD PRIMARY KEY (`meeting_id`);

--
-- Indexes for table `meeting_participants`
--
ALTER TABLE `meeting_participants`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `receiver_id` (`receiver_id`),
  ADD KEY `file_id` (`file_id`),
  ADD KEY `ix_messages_created_at` (`created_at`);

--
-- Indexes for table `message_reads`
--
ALTER TABLE `message_reads`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `message_id` (`message_id`,`reader_id`),
  ADD KEY `reader_id` (`reader_id`);

--
-- Indexes for table `pinned_messages`
--
ALTER TABLE `pinned_messages`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `group_id` (`group_id`,`group_message_id`),
  ADD KEY `group_message_id` (`group_message_id`),
  ADD KEY `pinned_by_id` (`pinned_by_id`);

--
-- Indexes for table `security_questions`
--
ALTER TABLE `security_questions`
  ADD PRIMARY KEY (`question_id`),
  ADD UNIQUE KEY `user_id` (`user_id`);

--
-- Indexes for table `system_settings`
--
ALTER TABLE `system_settings`
  ADD PRIMARY KEY (`setting_id`),
  ADD UNIQUE KEY `setting_key` (`setting_key`);

--
-- Indexes for table `temp_tokens`
--
ALTER TABLE `temp_tokens`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_users_user_id_str` (`user_id_str`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `alerts`
--
ALTER TABLE `alerts`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `audit_logs`
--
ALTER TABLE `audit_logs`
  MODIFY `log_id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=136;

--
-- AUTO_INCREMENT for table `files`
--
ALTER TABLE `files`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `groups`
--
ALTER TABLE `groups`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `group_members`
--
ALTER TABLE `group_members`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT for table `group_messages`
--
ALTER TABLE `group_messages`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `meetings`
--
ALTER TABLE `meetings`
  MODIFY `meeting_id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `meeting_participants`
--
ALTER TABLE `meeting_participants`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;

--
-- AUTO_INCREMENT for table `message_reads`
--
ALTER TABLE `message_reads`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `pinned_messages`
--
ALTER TABLE `pinned_messages`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `security_questions`
--
ALTER TABLE `security_questions`
  MODIFY `question_id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `system_settings`
--
ALTER TABLE `system_settings`
  MODIFY `setting_id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `temp_tokens`
--
ALTER TABLE `temp_tokens`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `alerts`
--
ALTER TABLE `alerts`
  ADD CONSTRAINT `alerts_ibfk_1` FOREIGN KEY (`triggered_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `alerts_ibfk_2` FOREIGN KEY (`message_id`) REFERENCES `messages` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `alerts_ibfk_3` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `alerts_ibfk_4` FOREIGN KEY (`resolved_by_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `files`
--
ALTER TABLE `files`
  ADD CONSTRAINT `files_ibfk_1` FOREIGN KEY (`uploader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `files_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `groups`
--
ALTER TABLE `groups`
  ADD CONSTRAINT `groups_ibfk_1` FOREIGN KEY (`created_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `group_members`
--
ALTER TABLE `group_members`
  ADD CONSTRAINT `group_members_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `group_members_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `group_messages`
--
ALTER TABLE `group_messages`
  ADD CONSTRAINT `group_messages_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `group_messages_ibfk_2` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `messages_ibfk_3` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE SET NULL;

--
-- Constraints for table `message_reads`
--
ALTER TABLE `message_reads`
  ADD CONSTRAINT `message_reads_ibfk_1` FOREIGN KEY (`message_id`) REFERENCES `messages` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `message_reads_ibfk_2` FOREIGN KEY (`reader_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `pinned_messages`
--
ALTER TABLE `pinned_messages`
  ADD CONSTRAINT `pinned_messages_ibfk_1` FOREIGN KEY (`group_id`) REFERENCES `groups` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `pinned_messages_ibfk_2` FOREIGN KEY (`group_message_id`) REFERENCES `group_messages` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `pinned_messages_ibfk_3` FOREIGN KEY (`pinned_by_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `temp_tokens`
--
ALTER TABLE `temp_tokens`
  ADD CONSTRAINT `temp_tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
