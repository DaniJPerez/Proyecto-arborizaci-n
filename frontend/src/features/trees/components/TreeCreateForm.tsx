import { router } from 'expo-router';
import { Controller } from 'react-hook-form';
import { Image, ScrollView, StyleSheet, Text, View } from 'react-native';

import type { Catalogos, GrupoObservacion, Institucion } from '@/features/catalogs/types';
import { useTreeCreateForm } from '@/features/trees/hooks/useTreeCreateForm';
import type { ArbolCrear, Etapa, FotoLocal, Interferencia, Zona } from '@/features/trees/types';
import { palette } from '@/config/constants';
import {
  ChoiceChip,
  Eyebrow,
  Field,
  Heading,
  InlineMessage,
  PrimaryButton,
  Screen,
  Section,
  SelectField,
  Surface,
} from '@/shared/components/FormControls';

const zonas: Zona[] = ['Patio central', 'Entrada principal', 'Zona deportiva', 'Bloques académicos', 'Otra'];
const etapas: Etapa[] = ['Plántula', 'Juvenil', 'Adulto', 'Senescente'];
const interferencias: Interferencia[] = [
  'Ninguna',
  'Levantamiento de pisos',
  'Afectación de muros',
  'Cables eléctricos',
  'Otra infraestructura',
];
const grupoLabels: Record<GrupoObservacion, string> = {
  follaje: 'Follaje',
  tronco: 'Tronco',
  raiz: 'Raíz',
  plagas: 'Plagas',
};

export function TreeCreateForm({
  catalogs,
  submitting,
  submitError,
  onSubmit,
}: {
  catalogs: Catalogos;
  submitting: boolean;
  submitError?: string;
  onSubmit: (values: ArbolCrear, photos: FotoLocal[]) => Promise<void>;
}) {
  const {
    control,
    errors,
    formError,
    gps,
    photos,
    zonaActual,
    interferenciaActual,
    observacionesActuales,
    pickPhoto,
    updateLocation,
    toggleObservation,
    submit,
  } = useTreeCreateForm(onSubmit);

  return (
    <Screen>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
        <View style={styles.topLine}>
          <PrimaryButton title="‹  Volver" variant="secondary" onPress={() => router.back()} />
          <Text style={styles.step}>NUEVO REGISTRO · 1 / 1</Text>
        </View>
        <Eyebrow>Identificación y captura</Eyebrow>
        <Heading subtitle="Selecciona los datos del catálogo y captura la ubicación del individuo en campo.">
          Añadir árbol
        </Heading>

        <Section title="Institución y zona">
          <Controller name="institucion_id" control={control} render={({ field }) => (
            <SelectField
              label="Institución"
              value={field.value || undefined}
              onChange={field.onChange}
              options={catalogs.instituciones.map((item: Institucion) => ({
                label: `${item.nombre_corto} · ${item.prefijo}`,
                value: item.id,
              }))}
              placeholder="Selecciona tu institución"
            />
          )} />
          {errors.institucion_id ? <InlineMessage>{errors.institucion_id.message}</InlineMessage> : null}
          <Controller name="zona" control={control} render={({ field }) => (
            <SelectField label="Zona del campus" value={field.value} onChange={field.onChange} options={zonas.map((value) => ({ label: value, value }))} />
          )} />
          {zonaActual === 'Otra' ? (
            <Controller name="zona_otra" control={control} render={({ field, fieldState }) => (
              <Field label="Nombre de la zona" value={field.value} onChangeText={field.onChange} error={fieldState.error?.message} placeholder="Describe la zona" />
            )} />
          ) : null}
          <Text style={styles.note}>El identificador se asigna automáticamente al guardar; no tienes que escribir un código.</Text>
        </Section>

        <Section title="Ubicación GPS">
          <Surface>
            <Text style={styles.coordinates}>
              {gps.location ? `${gps.location.lat.toFixed(6)}, ${gps.location.lng.toFixed(6)}` : 'Ubicación pendiente'}
            </Text>
            {gps.location?.accuracy != null ? <Text style={styles.note}>Precisión aproximada: {Math.round(gps.location.accuracy)} m</Text> : null}
            <View style={styles.gpsButton}><PrimaryButton title="⌖  Capturar ubicación actual" onPress={() => void updateLocation()} loading={gps.loading} /></View>
            {gps.error ? <InlineMessage>{gps.error}</InlineMessage> : null}
            {errors.gps_confirmado ? <InlineMessage>{errors.gps_confirmado.message}</InlineMessage> : null}
          </Surface>
        </Section>

        <Section title="Especie y dimensiones">
          <Controller name="especie_id" control={control} render={({ field }) => (
            <SelectField
              label="Especie"
              value={field.value || undefined}
              onChange={field.onChange}
              options={catalogs.especies.map((species) => ({ label: `${species.nombre_comun} · ${species.nombre_cientifico}`, value: species.id }))}
              placeholder="Selecciona la especie"
            />
          )} />
          {errors.especie_id ? <InlineMessage>{errors.especie_id.message}</InlineMessage> : null}
          <View style={styles.measurements}>
            <Controller name="dap_cm" control={control} render={({ field, fieldState }) => (
              <Field label="DAP (cm)" value={field.value?.toString() ?? ''} onChangeText={(text) => field.onChange(parseNumber(text))} keyboardType="decimal-pad" error={fieldState.error?.message} placeholder="Ej. 32.5" />
            )} />
            <Controller name="altura_m" control={control} render={({ field, fieldState }) => (
              <Field label="Altura (m)" value={field.value?.toString() ?? ''} onChangeText={(text) => field.onChange(parseNumber(text))} keyboardType="decimal-pad" error={fieldState.error?.message} placeholder="Ej. 8" />
            )} />
          </View>
          <Controller name="copa_m" control={control} render={({ field, fieldState }) => (
            <Field label="Diámetro de copa (m)" value={field.value?.toString() ?? ''} onChangeText={(text) => field.onChange(parseNumber(text))} keyboardType="decimal-pad" error={fieldState.error?.message} placeholder="Ej. 4.2" />
          )} />
          <Controller name="etapa" control={control} render={({ field }) => (
            <SelectField label="Etapa de desarrollo" value={field.value} onChange={field.onChange} options={etapas.map((value) => ({ label: value, value }))} />
          )} />
        </Section>

        <Section title="Observaciones fitosanitarias">
          <Text style={styles.note}>Marca solo lo que observas en el árbol. No escribas diagnósticos.</Text>
          {(['follaje', 'tronco', 'raiz', 'plagas'] as GrupoObservacion[]).map((group) => {
            const options = catalogs.observaciones.filter((item) => item.grupo === group);
            if (!options.length) return null;
            return (
              <View key={group} style={styles.observationGroup}>
                <Text style={styles.groupTitle}>{grupoLabels[group]}</Text>
                <View style={styles.chips}>
                  {options.map((item) => {
                    const selected = observacionesActuales.includes(item.codigo);
                    return <ChoiceChip key={item.codigo} label={item.etiqueta} selected={selected} onPress={() => {
                      toggleObservation(item.codigo);
                    }} />;
                  })}
                </View>
              </View>
            );
          })}
        </Section>

        <Section title="Interferencia observada">
          <Controller name="interferencia" control={control} render={({ field }) => (
            <SelectField label="Afectación a infraestructura" value={field.value} onChange={field.onChange} options={interferencias.map((value) => ({ label: value, value }))} />
          )} />
          {interferenciaActual === 'Otra infraestructura' ? (
            <Controller name="interferencia_otra" control={control} render={({ field, fieldState }) => (
              <Field label="¿Cuál infraestructura?" value={field.value} onChangeText={field.onChange} error={fieldState.error?.message} placeholder="Describe la afectación" />
            )} />
          ) : null}
        </Section>

        <Section title="Evidencia fotográfica">
          <Text style={styles.note}>La fotografía general es obligatoria. Puedes sumar una imagen de detalle.</Text>
          <View style={styles.photos}>
            <PhotoTile label="Árbol completo · Obligatoria" photo={photos.find((photo) => photo.tipo === 'completo')} onPress={() => void pickPhoto('completo')} />
            <PhotoTile label="Detalle · Opcional" photo={photos.find((photo) => photo.tipo === 'detalle')} onPress={() => void pickPhoto('detalle')} />
          </View>
        </Section>

        {formError || submitError ? <InlineMessage>{formError ?? submitError}</InlineMessage> : null}
        <PrimaryButton title="Guardar árbol" loading={submitting} onPress={submit} />
        <Text style={styles.disclaimer}>La calificación y el código del árbol se calculan o asignan en el servidor.</Text>
      </ScrollView>
    </Screen>
  );
}

function parseNumber(text: string) {
  if (!text.trim()) return undefined;
  const parsed = Number(text.replace(',', '.'));
  return Number.isFinite(parsed) ? parsed : undefined;
}

function PhotoTile({ label, photo, onPress }: { label: string; photo?: FotoLocal; onPress: () => void }) {
  return (
    <View style={styles.photoColumn}>
      <Text style={styles.photoLabel}>{label}</Text>
      <PrimaryButton title={photo ? 'Cambiar foto' : 'Abrir cámara'} variant="secondary" onPress={onPress} />
      {photo ? <Image source={{ uri: photo.uri }} style={styles.photoPreview} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 14, paddingBottom: 42, gap: 16 },
  topLine: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  step: { color: palette.muted, fontSize: 10, fontWeight: '800', letterSpacing: 0.8 },
  note: { color: palette.muted, fontSize: 12, lineHeight: 18 },
  coordinates: { marginBottom: 5, color: palette.ink, fontSize: 17, fontWeight: '800' },
  gpsButton: { marginTop: 13 },
  measurements: { flexDirection: 'row', gap: 10 },
  observationGroup: { gap: 8, marginBottom: 8 },
  groupTitle: { color: palette.muted, fontSize: 13, fontWeight: '800' },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  photos: { flexDirection: 'row', gap: 10 },
  photoColumn: { flex: 1, gap: 8 },
  photoLabel: { color: palette.ink, fontSize: 12, fontWeight: '700', minHeight: 32 },
  photoPreview: { width: '100%', height: 112, borderRadius: 8, backgroundColor: palette.line },
  disclaimer: { color: palette.muted, fontSize: 12, textAlign: 'center', lineHeight: 18 },
});