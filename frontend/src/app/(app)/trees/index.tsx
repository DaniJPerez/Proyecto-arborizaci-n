import { View, Text, StyleSheet } from 'react-native';
import TreeListScreen from '@/features/trees/components/TreeListScreen';

export default function TreesPage() {
  return (
    <View style={styles.container}>
      <View style={styles.previewBanner}>
        <Text style={styles.previewText}>
          MODO DE VISTA PREVIA · DATOS DE EJEMPLO
        </Text>
      </View>

      <View style={styles.content}>
        <TreeListScreen />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F4F7F2',
  },
  previewBanner: {
    backgroundColor: '#FFF3CD',
    padding: 10,
    alignItems: 'center',
  },
  previewText: {
    color: '#795900',
    fontSize: 11,
    fontWeight: '700',
  },
  content: {
    flex: 1,
  },
});