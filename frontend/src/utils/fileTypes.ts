/**
 * File type mapping utility
 * Maps file extensions to view types for appropriate viewer selection
 */

export type ViewType = 'text' | 'image' | 'video' | 'audio' | 'pdf' | 'code' | 'binary' | 'markdown' | 'json' | 'xml';

interface FileTypeMapping {
  viewType: ViewType;
  extensions: string[];
  mimeTypes?: string[];
}

const fileTypeMappings: FileTypeMapping[] = [
  // Images
  {
    viewType: 'image',
    extensions: ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico', 'tiff', 'tif', 'heic', 'heif', 'avif'],
  },
  // Videos
  {
    viewType: 'video',
    extensions: [
      'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v', 'flv', 'wmv', 'mpg', 'mpeg',
      '3gp', 'ogv', 'ts', 'mts', 'm2ts', 'vob', 'asf', 'rm', 'rmvb', 'divx'
    ],
  },
  // Audio
  {
    viewType: 'audio',
    extensions: [
      'mp3', 'wav', 'flac', 'aac', 'ogg', 'oga', 'm4a', 'wma', 'opus',
      'aiff', 'au', 'ra', 'amr', 'ac3', 'dts'
    ],
  },
  // PDF
  {
    viewType: 'pdf',
    extensions: ['pdf'],
  },
  // Code files
  {
    viewType: 'code',
    extensions: [
      'js', 'jsx', 'ts', 'tsx', 'py', 'java', 'cpp', 'c', 'h', 'hpp', 'cs',
      'php', 'rb', 'go', 'rs', 'swift', 'kt', 'scala', 'clj', 'hs', 'ml',
      'sh', 'bash', 'zsh', 'fish', 'ps1', 'bat', 'cmd', 'r', 'm', 'mm',
      'dart', 'lua', 'pl', 'pm', 'vim', 'vimrc', 'el', 'lisp', 'cl', 'sql',
      'html', 'htm', 'css', 'scss', 'sass', 'less', 'styl', 'vue', 'svelte',
      'xml', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'config', 'json',
      'dockerfile', 'makefile', 'cmake', 'gradle', 'maven', 'pom', 'build',
      'gradle', 'properties', 'log', 'txt', 'text', 'md', 'markdown'
    ],
  },
  // Markdown
  {
    viewType: 'markdown',
    extensions: ['md', 'markdown', 'mdown', 'mkdn', 'mkd'],
  },
  // JSON
  {
    viewType: 'json',
    extensions: ['json', 'jsonc', 'json5'],
  },
  // XML
  {
    viewType: 'xml',
    extensions: ['xml', 'xhtml', 'xsd', 'xsl', 'xslt'],
  },
  // Text files
  {
    viewType: 'text',
    extensions: [
      'txt', 'text', 'rtf', 'doc', 'docx', 'odt', 'csv', 'tsv',
      'readme', 'license', 'changelog', 'authors', 'contributors'
    ],
  },
];

// Create a reverse lookup map for fast extension -> viewType lookup
const extensionToViewType = new Map<string, ViewType>();

fileTypeMappings.forEach((mapping) => {
  mapping.extensions.forEach((ext) => {
    extensionToViewType.set(ext.toLowerCase(), mapping.viewType);
  });
});

/**
 * Get the view type for a file based on its extension
 * @param filename - The filename or path
 * @returns The view type, or 'binary' if unknown
 */
export function getViewType(filename: string): ViewType {
  const lower = filename.toLowerCase();
  const lastDot = lower.lastIndexOf('.');
  
  if (lastDot === -1 || lastDot === lower.length - 1) {
    // No extension or extension is empty
    return 'text'; // Default to text for files without extensions
  }
  
  const ext = lower.slice(lastDot + 1);
  return extensionToViewType.get(ext) || 'binary';
}

/**
 * Check if a file can be viewed (not binary or unknown type)
 * @param filename - The filename or path
 * @returns True if the file can be viewed
 */
export function canViewFile(filename: string): boolean {
  const viewType = getViewType(filename);
  return viewType !== 'binary';
}

/**
 * Get the display name for a view type
 * @param viewType - The view type
 * @returns Human-readable name
 */
export function getViewTypeName(viewType: ViewType): string {
  const names: Record<ViewType, string> = {
    text: 'Text',
    image: 'Image',
    video: 'Video',
    audio: 'Audio',
    pdf: 'PDF',
    code: 'Code',
    binary: 'Binary',
    markdown: 'Markdown',
    json: 'JSON',
    xml: 'XML',
  };
  return names[viewType] || 'Unknown';
}
