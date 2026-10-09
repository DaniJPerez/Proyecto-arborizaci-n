import { useMemo, useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  Pressable,
  View,
} from 'react-native';

type EstadoArbol = 'sano' | 'riesgo' | 'critico';

interface Arbol {
  id: string;
  codigo: string;
  nombre_comun: string;
  nombre_cientifico: string;
  zona: string;
  estado: EstadoArbol;
  altura_m: number;
}

const arbolesEjemplo: Arbol[] = [
  {
    id: '1',
    codigo: 'ARB-001',
    nombre_comun: 'Ceiba',
    nombre_cientifico: 'Ceiba pentandra',
    zona: 'Zona norte',
    estado: 'sano',
    altura_m: 8.5,
  },
  {
    id: '2',
    codigo: 'ARB-002',
    nombre_comun: 'Roble',
    nombre_cientifico: 'Tabebuia rosea',
    zona: 'Zona central',
    estado: 'riesgo',
    altura_m: 5.2,
  },
  {
    id: '3',
    codigo: 'ARB-003',
    nombre_comun: 'Guayacán',
    nombre_cientifico: 'Handroanthus chrysanthus',
    zona: 'Zona sur',
    estado: 'critico',
    altura_m: 4.3,
  },
];

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

export default function TreeListScreen() {
  const [busqueda, setBusqueda] = useState('');
  const [filtro, setFiltro] = useState<string>('todos');

  const arbolesFiltrados = useMemo(() => {
    const texto = busqueda.trim().toLowerCase();

    return arbolesEjemplo.filter((arbol) => {
      const coincideTexto = [
        arbol.codigo,
        arbol.nombre_comun,
        arbol.nombre_cientifico,
        arbol.zona,
      ].some((valor) => valor.toLowerCase().includes(texto));

      const coincideEstado =
        filtro === 'todos' || arbol.estado === filtro;

      return coincideTexto && coincideEstado;
    });
  }, [busqueda, filtro]);

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>GESTIÓN AMBIENTAL</Text>
        <Text style={styles.title}>Inventario de árboles</Text>
        <Text style={styles.subtitle}>
          Consulta y organiza los árboles registrados.
        </Text>
      </View>

      <View style={styles.summary}>
        <Text style={styles.summaryLabel}>Árboles encontrados</Text>
        <Text style={styles.summaryNumber}>
          {arbolesFiltrados.length}
        </Text>
      </View>

      <TextInput
        style={styles.search}
        placeholder="Buscar por nombre, código o zona..."
        placeholderTextColor="#7A8A80"
        value={busqueda}
        onChangeText={setBusqueda}
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

      <Text style={styles.sectionTitle}>Registros</Text>

      {arbolesFiltrados.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyTitle}>No hay resultados</Text>
          <Text style={styles.emptyText}>
            Prueba con otro nombre o selecciona otro filtro.
          </Text>
        </View>
      ) : (
        arbolesFiltrados.map((arbol) => (
          <View key={arbol.id} style={styles.card}>
            <View style={styles.cardHeader}>
              <View style={styles.treeIcon}>
                <Text style={styles.treeEmoji}>🌳</Text>
              </View>

              <View style={styles.treeInfo}>
                <Text style={styles.treeName}>{arbol.nombre_comun}</Text>
                <Text style={styles.scientificName}>
                  {arbol.nombre_cientifico}
                </Text>
                <Text style={styles.code}>{arbol.codigo}</Text>
              </View>
            </View>

            <View style={styles.divider} />

            <View style={styles.details}>
              <View>
                <Text style={styles.detailLabel}>Ubicación</Text>
                <Text style={styles.detailValue}>{arbol.zona}</Text>
              </View>

              <View>
                <Text style={styles.detailLabel}>Altura</Text>
                <Text style={styles.detailValue}>
                  {arbol.altura_m} m
                </Text>
              </View>
            </View>

            <View
              style={[
                styles.status,
                { backgroundColor: `${coloresEstado[arbol.estado]}15` },
              ]}
            >
              <View
                style={[
                  styles.statusDot,
                  { backgroundColor: coloresEstado[arbol.estado] },
                ]}
              />
              <Text
                style={[
                  styles.statusText,
                  { color: coloresEstado[arbol.estado] },
                ]}
              >
                {etiquetasEstado[arbol.estado]}
              </Text>
            </View>
          </View>
        ))
      )}

      <Text style={styles.note}>
        Prototipo visual: los registros mostrados son datos de ejemplo.
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
  sectionTitle: {
    color: '#203D2C',
    fontSize: 18,
    fontWeight: '800',
    marginBottom: 12,
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
    marginBottom: 14,
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
  empty: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 25,
    alignItems: 'center',
  },
  emptyTitle: {
    color: '#203D2C',
    fontSize: 16,
    fontWeight: '800',
  },
  emptyText: {
    color: '#68796C',
    fontSize: 13,
    textAlign: 'center',
    marginTop: 8,
  },
  note: {
    color: '#849087',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 12,
  },
});