<script setup lang="ts">
import { computed } from 'vue';
import { getViewType } from '@/utils/fileTypes';
import { useAppContext } from '@/context/appContext';
import TextViewer from './viewers/TextViewer.vue';
import CodeViewer from './viewers/CodeViewer.vue';
import ImageViewer from './viewers/ImageViewer.vue';
import VideoViewer from './viewers/VideoViewer.vue';
import AudioViewer from './viewers/AudioViewer.vue';
import PDFViewer from './viewers/PDFViewer.vue';
import MarkdownViewer from './viewers/MarkdownViewer.vue';
import JSONViewer from './viewers/JSONViewer.vue';
import XMLViewer from './viewers/XMLViewer.vue';
import BinaryViewer from './viewers/BinaryViewer.vue';

const props = defineProps<{
  filePath: string;
}>();

const { storageType } = useAppContext();
const viewType = computed(() => getViewType(props.filePath));

const viewerComponent = computed(() => {
  switch (viewType.value) {
    case 'text':
      return TextViewer;
    case 'code':
      return CodeViewer;
    case 'image':
      return ImageViewer;
    case 'video':
      return VideoViewer;
    case 'audio':
      return AudioViewer;
    case 'pdf':
      return PDFViewer;
    case 'markdown':
      return MarkdownViewer;
    case 'json':
      return JSONViewer;
    case 'xml':
      return XMLViewer;
    case 'binary':
    default:
      return BinaryViewer;
  }
});
</script>

<template>
  <div class="w-full">
    <component :is="viewerComponent" :file-path="filePath" :storage-type="storageType" />
  </div>
</template>
