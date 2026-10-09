import { z } from 'zod';

export const arbolCreateSchema = z.object({
  institucion_id: z.string().min(1, 'Selecciona la institución.'),
  zona: z.enum([
    'Patio central',
    'Entrada principal',
    'Zona deportiva',
    'Bloques académicos',
    'Otra',
  ]),
  zona_otra: z.string().max(120).optional(),
  lat: z.number().min(-90).max(90),
  lng: z.number().min(-180).max(180),
  gps_confirmado: z.boolean().refine(Boolean, 'Captura la ubicación GPS.'),
  especie_id: z.number().int().positive('Selecciona una especie.'),
  dap_cm: z.number().gt(0, 'Debe ser mayor que cero.'),
  altura_m: z.number().gt(0).max(25, 'Máximo 25 m.'),
  copa_m: z.number().gt(0),
  etapa: z.enum(['Plántula', 'Juvenil', 'Adulto', 'Senescente']),
  interferencia: z.enum([
    'Ninguna',
    'Levantamiento de pisos',
    'Afectación de muros',
    'Cables eléctricos',
    'Otra infraestructura',
  ]),
  interferencia_otra: z.string().max(120).optional(),
  observaciones: z.array(z.string()),
}).superRefine((value, ctx) => {
  if (value.zona === 'Otra' && !value.zona_otra?.trim()) {
    ctx.addIssue({ code: 'custom', path: ['zona_otra'], message: 'Especifica la zona.' });
  }
  if (value.interferencia === 'Otra infraestructura' && !value.interferencia_otra?.trim()) {
    ctx.addIssue({
      code: 'custom',
      path: ['interferencia_otra'],
      message: 'Describe la infraestructura afectada.',
    });
  }
});

export type ArbolFormInput = z.input<typeof arbolCreateSchema>;