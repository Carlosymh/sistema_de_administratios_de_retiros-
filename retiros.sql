-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 27-01-2022 a las 03:41:04
-- Versión del servidor: 10.4.21-MariaDB
-- Versión de PHP: 8.0.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `retiros_2`
--
CREATE DATABASE IF NOT EXISTS `retiros_2` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `retiros_2`;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `donacion`
--

DROP TABLE IF EXISTS `donacion`;
CREATE TABLE `donacion` (
  `id_donacion` bigint(110) NOT NULL,
  `nuemro_de_ola` bigint(110) NOT NULL,
  `SKU` varchar(255) NOT NULL,
  `cantidad` bigint(110) NOT NULL,
  `ubicacion` varchar(255) NOT NULL,
  `responsable` varchar(255) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ingram`
--

DROP TABLE IF EXISTS `ingram`;
CREATE TABLE `ingram` (
  `id_solicitud` bigint(110) NOT NULL,
  `numero_ola` bigint(20) NOT NULL,
  `SKU` varchar(255) NOT NULL,
  `Cantidad_Solicitada` bigint(110) NOT NULL,
  `cantidad_disponible` bigint(110) NOT NULL,
  `piezas_surtidas` bigint(110) DEFAULT 0,
  `descripcion` varchar(255) NOT NULL,
  `estatus` varchar(255) DEFAULT 'Pendiente',
  `ubicacion` varchar(255) DEFAULT NULL,
  `fecha_de_solicitud` date NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario_seller`
--

DROP TABLE IF EXISTS `inventario_seller`;
CREATE TABLE `inventario_seller` (
  `INVENTORY_ID` varchar(110) NOT NULL,
  `ADDRESS_ID_TO` varchar(255) NOT NULL,
  `Seller` varchar(255) NOT NULL,
  `Holding` varchar(255) NOT NULL,
  `Cantidad` bigint(110) NOT NULL,
  `fecha_de_actualizacion` date NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `retirio_ingram`
--

DROP TABLE IF EXISTS `retirio_ingram`;
CREATE TABLE `retirio_ingram` (
  `id_retiro` bigint(20) NOT NULL,
  `nuemro_de_ola` bigint(110) NOT NULL,
  `SKU` varchar(255) NOT NULL,
  `cantidad` bigint(110) NOT NULL,
  `ubicacion` varchar(255) NOT NULL,
  `responsable` varchar(255) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `retiros`
--

DROP TABLE IF EXISTS `retiros`;
CREATE TABLE `retiros` (
  `id_retiro` bigint(20) NOT NULL,
  `nuemro_de_ola` bigint(20) NOT NULL,
  `meli` varchar(255) NOT NULL,
  `cantidad` bigint(110) NOT NULL,
  `ubicacion` varchar(255) NOT NULL,
  `responsable` varchar(255) NOT NULL,
  `fecha` date NOT NULL,
  `fecha_hora` datetime NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

DROP TABLE IF EXISTS `roles`;
CREATE TABLE `roles` (
  `ID` bigint(100) NOT NULL,
  `Nombre` varchar(250) NOT NULL,
  `Apellido` varchar(255) NOT NULL,
  `Usuario` varchar(70) NOT NULL,
  `facility` varchar(250) NOT NULL,
  `Site` varchar(255) NOT NULL,
  `Rango` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`ID`, `Nombre`, `Apellido`, `Usuario`, `facility`, `Site`, `Rango`) VALUES
(60, 'admintrador', '01', 'admin01', 'Fulfillment', 'Odonnell', 'Administrador');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `solicitud_donacion`
--

DROP TABLE IF EXISTS `solicitud_donacion`;
CREATE TABLE `solicitud_donacion` (
  `id_donacion` bigint(110) NOT NULL,
  `numero_ola` bigint(20) NOT NULL,
  `SKU` varchar(255) NOT NULL,
  `Cantidad_Solicitada` bigint(110) NOT NULL,
  `costo_unitario` float NOT NULL,
  `suma_de_gmv_total` float NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `cantidad_susrtida` bigint(20) NOT NULL,
  `status` varchar(255) DEFAULT 'Pendiente',
  `ubicacion` varchar(255) DEFAULT NULL,
  `fecha_de_solicitud` date NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `solicitud_retiros`
--

DROP TABLE IF EXISTS `solicitud_retiros`;
CREATE TABLE `solicitud_retiros` (
  `id_tarea_retiros` bigint(11) NOT NULL,
  `nuemro_de_ola` bigint(110) NOT NULL,
  `meli` varchar(255) NOT NULL,
  `fecha_de_entrega` date NOT NULL,
  `cantidad_solizitada` bigint(110) NOT NULL,
  `QTY_DISP_WMS` bigint(110) NOT NULL,
  `Descripción` varchar(255) NOT NULL,
  `cantidad_susrtida` bigint(110) DEFAULT 0,
  `status` varchar(255) DEFAULT 'Pendiente',
  `ubicacion` varchar(255) DEFAULT NULL,
  `Fecha_de_creacion` date NOT NULL,
  `facility` varchar(255) NOT NULL,
  `Site` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `donacion`
--
ALTER TABLE `donacion`
  ADD PRIMARY KEY (`id_donacion`);

--
-- Indices de la tabla `ingram`
--
ALTER TABLE `ingram`
  ADD PRIMARY KEY (`id_solicitud`);

--
-- Indices de la tabla `retirio_ingram`
--
ALTER TABLE `retirio_ingram`
  ADD PRIMARY KEY (`id_retiro`);

--
-- Indices de la tabla `retiros`
--
ALTER TABLE `retiros`
  ADD PRIMARY KEY (`id_retiro`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`ID`);

--
-- Indices de la tabla `solicitud_donacion`
--
ALTER TABLE `solicitud_donacion`
  ADD PRIMARY KEY (`id_donacion`);

--
-- Indices de la tabla `solicitud_retiros`
--
ALTER TABLE `solicitud_retiros`
  ADD PRIMARY KEY (`id_tarea_retiros`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `donacion`
--
ALTER TABLE `donacion`
  MODIFY `id_donacion` bigint(110) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `ingram`
--
ALTER TABLE `ingram`
  MODIFY `id_solicitud` bigint(110) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `retirio_ingram`
--
ALTER TABLE `retirio_ingram`
  MODIFY `id_retiro` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `retiros`
--
ALTER TABLE `retiros`
  MODIFY `id_retiro` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `roles`
--
ALTER TABLE `roles`
  MODIFY `ID` bigint(100) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=65;

--
-- AUTO_INCREMENT de la tabla `solicitud_donacion`
--
ALTER TABLE `solicitud_donacion`
  MODIFY `id_donacion` bigint(110) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `solicitud_retiros`
--
ALTER TABLE `solicitud_retiros`
  MODIFY `id_tarea_retiros` bigint(11) NOT NULL AUTO_INCREMENT;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
