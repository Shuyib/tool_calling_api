/**
 * Data models using Zod for validation
 */

import { z } from 'zod';

/**
 * Line item schema for receipts
 */
export const LineItemSchema = z.object({
  description: z.string(),
  quantity: z.number().optional(),
  price: z.number().optional(),
  total: z.number().optional(),
});

/**
 * Receipt data schema
 */
export const ReceiptDataSchema = z.object({
  merchant_name: z.string().optional(),
  merchant_address: z.string().optional(),
  date: z.string().optional(),
  receipt_number: z.string().optional(),
  line_items: z.array(LineItemSchema).optional(),
  subtotal: z.number().optional(),
  tax: z.number().optional(),
  total: z.number().optional(),
  payment_method: z.string().optional(),
  raw_text: z.string().optional(),
});

export const LineItem = LineItemSchema;
export const ReceiptData = ReceiptDataSchema;
