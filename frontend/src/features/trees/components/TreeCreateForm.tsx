import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  Pressable,
  View,
} from 'react-native';
import { useQuery } from '@tanstack/react-query';

import { treesService } from '@/features/trees/services/treesService';
import type { ArbolResumen } from '@/shared/types/entities';

type EstadoArbol = 'sano' | 'riesgo' | 'critico';

const filtros = [
  { label: 'Todos', value: 'todos' },
  { label: 'Sanos', value: 'sano' },
  { label: 'En riesgo', value: 'riesgo' },
  { label: 'Críticos', value: 'critico' },
] as const;

const coloresEstado: Record<EstadoArbol, string> = {
  sano: '#15803D',
  riesgo: '#B45309',
  critico: '#B91C1C',
};

const etiquetasEstado: Record<EstadoArbol, string> = {
  sano: 'Sano',
  riesgo: 'En riesgo',
  critico: 'Crítico',
};

function normalizarEstado(estado: string): EstadoArbol {
  if (estado === 'riesgo' || estado === 'critico') {
    return estado;
  }

  return 'sano';
}

export default function TreeListScreen() {
  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState<string>('todos');

  const {
    data: arboles = [],
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<ArbolResumen[]>({
    queryKey: ['arboles'],
    queryFn: treesService.getAll,
  });

  const arbolesFiltrados = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();

    return arboles.filter((arbol) => {
      const coincideTexto = [
        arbol.codigo,
        arbol.nombre_comun,
        arbol.nombre_cientifico,
        arbol.zona,
        arbol.nombre_corto,
      ].some((valor) => String(valor ?? '').toLowerCase().includes(texto));

      const estado = normalizarEstado(arbol.estado);
      const coincideEstado = filtro === 'todos' || estado === filtro;

      return coincideTexto && coincideEstado;
    });
  }, [arboles, busqueda, filtro]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
    >
      <View style={styles.header}>
        <Text style={styles.eyebrow}>GESTIÓN AMBIENTAL</Text>

        <Text style={styles.title}>Inventario de árboles</Text>

        <Text style={styles.subtitle}>
          Consulta y organiza los árboles registrados en el sistema.
        </Text>
      </View>

      <View style={styles.summary}>
        <Text style={styles.summaryLabel}>Árboles encontrados</Text>

        <Text style={styles.summaryNumber}>
          {isLoading ? '...' : arbolesFiltrados.length}
        </Text>

        <Text style={styles.summaryDescription}>
          Registros disponibles en el inventario
        </Text>
      </View>

      <TextInput
        style={styles.search}
        placeholder="Buscar por nombre, código o zona..."
        placeholderTextColor="#7A8A80"
        value={busqueda}
        onChangeText={setBusqueda}
        accessibilityLabel="Buscar árboles"
      />

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filters}
      >
        {filtros.map((item) => {
          const seleccionado = filtro === item.value;

          return (
            <Pressable
              key={item.value}
              onPress={() => setFiltro(item.value)}
              style={[
                styles.filterButton,
                seleccionado && styles.filterSelected,
              ]}
            >
              <Text
                style={[
                  styles.filterText,
                  seleccionado && styles.filterTextSelected,
                ]}
              >
                {item.label}
              </Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Registros</Text>

        {!isLoading && !isError && (
          <Text style={styles.resultCount}>
            {arbolesFiltrados.length} resultados
          </Text>
        )}
      </View>

      {isLoading ? (
        <View style={styles.messageCard}>
          <ActivityIndicator size="large" color="#1D5638" />

          <Text style={styles.messageTitle}>Cargando inventario...</Text>

          <Text style={styles.messageText}>
            Estamos consultando los árboles registrados.
          </Text>
        </View>
      ) : isError ? (
        <View style={styles.messageCard}>
          <Text style={styles.errorIcon}>!</Text>

          <Text style={styles.messageTitle}>
            No pudimos cargar los árboles
          </Text>

          <Text style={styles.messageText}>
            {error instanceof Error
              ? error.message
              : 'Comprueba la conexión con el servidor e inténtalo de nuevo.'}
          </Text>

          <Pressable style={styles.retryButton} onPress={() => void refetch()}>
            <Text style={styles.retryButtonText}>Reintentar</Text>
          </Pressable>
        </View>
      ) : arbolesFiltrados.length === 0 ? (
        <View style={styles.messageCard}>
          <Text style={styles.emptyEmoji}>🌱</Text>

          <Text style={styles.messageTitle}>
            {arboles.length === 0
              ? 'Todavía no hay árboles registrados'
              : 'No hay resultados'}
          </Text>

          <Text style={styles.messageText}>
            {arboles.length === 0
              ? 'Cuando existan registros en el sistema, aparecerán aquí.'
              : 'Prueba con otro nombre o selecciona un filtro diferente.'}
          </Text>
        </View>
      ) : (
        <>
          {arbolesFiltrados.map((arbol) => {
            const estado = normalizarEstado(arbol.estado);
            const color = coloresEstado[estado];

            return (
              <View key={arbol.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  <View style={styles.treeIcon}>
                    <Text style={styles.treeEmoji}>🌳</Text>
                  </View>

                  <View style={styles.treeInfo}>
                    <Text style={styles.treeName}>
                      {arbol.nombre_comun || 'Árbol sin nombre'}
                    </Text>

                    <Text style={styles.scientificName}>
                      {arbol.nombre_cientifico || 'Especie no especificada'}
                    </Text>

                    <Text style={styles.code}>
                      Código: {arbol.codigo}
                    </Text>
                  </View>
                </View>

                <View style={styles.divider} />

                <View style={styles.details}>
                  <View style={styles.detailColumn}>
                    <Text style={styles.detailLabel}>Zona</Text>

                    <Text style={styles.detailValue}>
                      {arbol.zona === 'Otra' && arbol.zona_otra
                        ? arbol.zona_otra
                        : arbol.zona || 'Sin ubicación'}
                    </Text>
                  </View>

                  <View style={styles.detailColumn}>
                    <Text style={styles.detailLabel}>Altura</Text>

                    <Text style={styles.detailValue}>
                      {Number(arbol.altura_m).toLocaleString('es-CO')} m
                    </Text>
                  </View>
                </View>

                <View style={styles.details}>
                  <View style={styles.detailColumn}>
                    <Text style={styles.detailLabel}>Diámetro del tronco</Text>

                    <Text style={styles.detailValue}>
                      {Number(arbol.dap_cm).toLocaleString('es-CO')} cm
                    </Text>
                  </View>

                  <View style={styles.detailColumn}>
                    <Text style={styles.detailLabel}>Etapa</Text>

                    <Text style={styles.detailValue}>
                      {arbol.etapa || 'No especificada'}
                    </Text>
                  </View>
                </View>

                <View
                  style={[
                    styles.status,
                    { backgroundColor: `${color}15` },
                  ]}
                >
                  <View
                    style={[styles.statusDot, { backgroundColor: color }]}
                  />

                  <Text style={[styles.statusText, { color }]}>
                    {etiquetasEstado[estado]}
                  </Text>
                </View>
              </View>
            );
          })}

          {isFetching && (
            <Text style={styles.refreshText}>Actualizando registros...</Text>
          )}
        </>
      )}

      <Text style={styles.note}>
        La información se obtiene de la API del proyecto.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4F7F2',
  },
  content: {
    padding: 20,
    paddingBottom: 40,
    width: '100%',
    maxWidth: 850,
    alignSelf: 'center',
  },
  header: {
    marginBottom: 22,
  },
  eyebrow: {
    color: '#287447',
    fontSize: 11,
    fontWeight: '800',
    letterSpacing: 1.5,
    marginBottom: 8,
  },
  title: {
    color: '#173D2A',
    fontSize: 28,
    fontWeight: '800',
  },
  subtitle: {
    color: '#65766A',
    fontSize: 14,
    marginTop: 8,
    lineHeight: 21,
  },
  summary: {
    backgroundColor: '#1D5638',
    borderRadius: 18,
    padding: 20,
    marginBottom: 18,
  },
  summaryLabel: {
    color: '#D8E9DB',
    fontSize: 13,
  },
  summaryNumber: {
    color: '#FFFFFF',
    fontSize: 34,
    fontWeight: '800',
    marginTop: 5,
  },
  summaryDescription: {
    color: '#D8E9DB',
    fontSize: 12,
    marginTop: 4,
  },
  search: {
    backgroundColor: '#FFFFFF',
    borderColor: '#DCE5DA',
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 15,
    paddingVertical: 14,
    fontSize: 14,
    color: '#203D2C',
    marginBottom: 15,
  },
  filters: {
    gap: 8,
    paddingBottom: 18,
  },
  filterButton: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 22,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#DCE5DA',
  },
  filterSelected: {
    backgroundColor: '#1D5638',
    borderColor: '#1D5638',
  },
  filterText: {
    color: '#4E6254',
    fontSize: 13,
    fontWeight: '600',
  },
  filterTextSelected: {
    color: '#FFFFFF',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    color: '#203D2C',
    fontSize: 18,
    fontWeight: '800',
  },
  resultCount: {
    color: '#68796C',
    fontSize: 12,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E3EAE0',
    padding: 17,
    marginBottom: 13,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 13,
  },
  treeIcon: {
    width: 52,
    height: 52,
    borderRadius: 15,
    backgroundColor: '#E8F2E5',
    justifyContent: 'center',
    alignItems: 'center',
  },
  treeEmoji: {
    fontSize: 27,
  },
  treeInfo: {
    flex: 1,
  },
  treeName: {
    color: '#203D2C',
    fontSize: 17,
    fontWeight: '800',
  },
  scientificName: {
    color: '#68796C',
    fontSize: 12,
    fontStyle: 'italic',
    marginTop: 3,
  },
  code: {
    color: '#287447',
    fontSize: 11,
    fontWeight: '700',
    marginTop: 5,
  },
  divider: {
    height: 1,
    backgroundColor: '#EDF1EA',
    marginVertical: 15,
  },
  details: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
    marginBottom: 14,
  },
  detailColumn: {
    flex: 1,
  },
  detailLabel: {
    color: '#7A8A7D',
    fontSize: 11,
    marginBottom: 5,
  },
  detailValue: {
    color: '#344D3B',
    fontSize: 13,
    fontWeight: '700',
  },
  status: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 11,
    paddingVertical: 7,
    borderRadius: 20,
    gap: 7,
  },
  statusDot: {
    width: 7,
    height: 7,
    borderRadius: 4,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '700',
  },
  messageCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E3EAE0',
    padding: 25,
    alignItems: 'center',
    marginBottom: 14,
  },
  messageTitle: {
    color: '#203D2C',
    fontSize: 16,
    fontWeight: '800',
    textAlign: 'center',
    marginTop: 12,
  },
  messageText: {
    color: '#68796C',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  errorIcon: {
    color: '#B91C1C',
    fontSize: 28,
    fontWeight: '800',
  },
  retryButton: {
    backgroundColor: '#1D5638',
    borderRadius: 10,
    paddingHorizontal: 20,
    paddingVertical: 11,
    marginTop: 16,
  },
  retryButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '700',
  },
  emptyEmoji: {
    fontSize: 34,
  },
  refreshText: {
    color: '#68796C',
    fontSize: 12,
    textAlign: 'center',
    marginVertical: 8,
  },
  note: {
    color: '#849087',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 12,
  },
});