/**
 * Logging utility using Winston
 */

import winston from 'winston';
import DailyRotateFile from 'winston-daily-rotate-file';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Creates a logger with file and console transports
 * 
 * @param {string} filename - Name of the log file (without extension)
 * @returns {winston.Logger} Configured Winston logger
 */
export function createLogger(filename = 'app') {
  const format = winston.format.combine(
    winston.format.timestamp({
      format: 'YYYY-MM-DD HH:mm:ss',
    }),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.printf(({ timestamp, level, message, ...meta }) => {
      let msg = `${timestamp}:${filename}:${level.toUpperCase()}:${message}`;
      if (Object.keys(meta).length > 0) {
        msg += ` ${JSON.stringify(meta)}`;
      }
      return msg;
    })
  );

  const logger = winston.createLogger({
    level: process.env.LOG_LEVEL || 'info',
    format,
    transports: [
      // Console transport
      new winston.transports.Console({
        level: 'debug',
        format: winston.format.combine(
          winston.format.colorize(),
          format
        ),
      }),
      // File transport with rotation
      new DailyRotateFile({
        filename: `${filename}-%DATE%.log`,
        datePattern: 'YYYY-MM-DD',
        maxSize: '5m',
        maxFiles: '5d',
        level: 'info',
      }),
    ],
  });

  return logger;
}

// Create a default logger
export const logger = createLogger('app');
