export type Zona =
  | 'Patio central'
  | 'Entrada principal'
  | 'Zona deportiva'
  | 'Bloques académicos'
  | 'Otra';
export type Etapa = 'Plántula' | 'Juvenil' | 'Adulto' | 'Senescente';
export type Interferencia =
  | 'Ninguna'
  | 'Levantamiento de pisos'
  | 'Afectación de muros'
  | 'Cables eléctricos'
  | 'Otra infraestructura';
export type TipoFoto = 'completo' | 'detalle' | 'adicional';

export interface ArbolCrear {
  institucion_id: string;
  zona: Zona;
  zona_otra?: string | null;
  lat: number;
  lng: number;
  especie_id: number;
  dap_cm: number;
  altura_m: number;
  copa_m: number;
  etapa: Etapa;
  interferencia: Interferencia;
  interferencia_otra?: string | null;
  observaciones: string[];
}

export interface FotoLocal {
  tipo: TipoFoto;
  uri: string;
  name: string;
  mimeType: string;
}