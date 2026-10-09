import { zodResolver } from '@hookform/resolvers/zod';
import * as ImagePicker from 'expo-image-picker';
import { useState } from 'react';
import { useForm, useWatch } from 'react-hook-form';

import { useCaptureLocation } from '@/features/trees/hooks/useCaptureLocation';
import { arbolCreateSchema, type ArbolFormInput } from '@/features/trees/schemas';
import type { ArbolCrear, FotoLocal } from '@/features/trees/types';

export function useTreeCreateForm(onSubmit: (values: ArbolCrear, photos: FotoLocal[]) => Promise<void>) {
  const [photos, setPhotos] = useState<FotoLocal[]>([]);
  const [formError, setFormError] = useState<string>();
  const gps = useCaptureLocation();
  const { control, handleSubmit, setValue, formState: { errors } } = useForm<ArbolFormInput>({
    resolver: zodResolver(arbolCreateSchema),
    defaultValues: {
      institucion_id: '',
      zona: 'Patio central',
      zona_otra: '',
      lat: 0,
      lng: 0,
      gps_confirmado: false,
      especie_id: 0,
      dap_cm: undefined,
      altura_m: undefined,
      copa_m: undefined,
      etapa: 'Adulto',
      interferencia: 'Ninguna',
      interferencia_otra: '',
      observaciones: [],
    },
  });

  const zonaActual = useWatch({ control, name: 'zona' });
  const interferenciaActual = useWatch({ control, name: 'interferencia' });
  const observacionesActuales = useWatch({ control, name: 'observaciones' }) ?? [];

  async function pickPhoto(tipo: FotoLocal['tipo']) {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      setFormError('Permite el acceso a la cámara para tomar evidencia del árbol.');
      return;
    }
    const result = await ImagePicker.launchCameraAsync({ mediaTypes: ['images'], quality: 0.85 });
    if (result.canceled || !result.assets[0]) return;
    const asset = result.assets[0];
    setPhotos((current) => [
      ...current.filter((photo) => photo.tipo !== tipo),
      {
        tipo,
        uri: asset.uri,
        name: asset.fileName ?? `${tipo}-${Date.now()}.jpg`,
        mimeType: asset.mimeType ?? 'image/jpeg',
      },
    ]);
    setFormError(undefined);
  }

  async function updateLocation() {
    const value = await gps.capture();
    if (!value) return;
    setValue('lat', value.lat, { shouldValidate: true });
    setValue('lng', value.lng, { shouldValidate: true });
    setValue('gps_confirmado', true, { shouldValidate: true });
  }

  function toggleObservation(code: string) {
    const updated = observacionesActuales.includes(code)
      ? observacionesActuales.filter((value) => value !== code)
      : [...observacionesActuales, code];
    setValue('observaciones', updated, { shouldValidate: true });
  }

  const submit = handleSubmit(async (input) => {
    setFormError(undefined);
    if (!photos.some((photo) => photo.tipo === 'completo')) {
      setFormError('Toma una fotografía general del árbol antes de guardar.');
      return;
    }
    const payload: ArbolCrear = {
      institucion_id: input.institucion_id,
      zona: input.zona,
      zona_otra: input.zona_otra,
      lat: input.lat,
      lng: input.lng,
      especie_id: input.especie_id,
      dap_cm: input.dap_cm,
      altura_m: input.altura_m,
      copa_m: input.copa_m,
      etapa: input.etapa,
      interferencia: input.interferencia,
      interferencia_otra: input.interferencia_otra,
      observaciones: input.observaciones,
    };
    await onSubmit(payload, photos);
  });

  return {
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
  };
}