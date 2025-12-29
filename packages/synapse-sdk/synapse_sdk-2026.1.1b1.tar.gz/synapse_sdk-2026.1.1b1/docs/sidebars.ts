import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';
import apiReferenceSidebar from './docs/api/reference/sidebar.json';

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.
 */
const sidebars: SidebarsConfig = {
  tutorialSidebar: [
    'introduction',
    'installation', 
    'quickstart',
    {
      type: 'category',
      label: 'Features',
      items: [
        'features/features',
        'features/converters/converters',
      ],
    },
    {
      type: 'category',
      label: 'Utilities',
      items: [
        'features/utils/file',
        'features/utils/network',
        'features/utils/storage',
        'features/utils/types',
      ],
    },
    {
      type: 'category',
      label: 'Plugin System',
      items: [
        'plugins/plugins',
        'plugins/export-plugins',
        {
          type: 'category',
          label: 'Upload Plugins',
          link: {
            type: 'doc',
            id: 'plugins/categories/upload-plugins/upload-plugin-overview',
          },
          items: [
            'plugins/categories/upload-plugins/upload-plugin-overview',
            'plugins/categories/upload-plugins/upload-plugin-action',
            'plugins/categories/upload-plugins/upload-plugin-template',
          ],
        },
        {
          type: 'category',
          label: 'Pre-annotation Plugins',
          link: {
            type: 'doc',
            id: 'plugins/categories/pre-annotation-plugins/pre-annotation-plugin-overview',
          },
          items: [
            'plugins/categories/pre-annotation-plugins/pre-annotation-plugin-overview',
            'plugins/categories/pre-annotation-plugins/to-task-overview',
            'plugins/categories/pre-annotation-plugins/to-task-action-development',
            'plugins/categories/pre-annotation-plugins/to-task-template-development',
          ],
        },
        {
          type: 'category',
          label: 'Neural Network Plugins',
          link: {
            type: 'doc',
            id: 'plugins/categories/neural-net-plugins/train-action-overview',
          },
          items: [
            'plugins/categories/neural-net-plugins/train-action-overview',
            'plugins/categories/neural-net-plugins/gradio-playground',
          ],
        },
      ],
    },
    {
      type: 'category',
      label: 'API Clients',
      items: [
        'api/index',
        {
          type: 'category',
          label: 'Clients',
          items: [
            'api/clients/index',
            'api/clients/backend',
            'api/clients/annotation-mixin',
            'api/clients/core-mixin',
            'api/clients/data-collection-mixin',
            'api/clients/hitl-mixin',
            'api/clients/integration-mixin',
            'api/clients/ml-mixin',
            'api/clients/agent',
            'api/clients/ray',
            'api/clients/base',
          ],
        },
        {
          type: 'category',
          label: 'Plugins',
          items: [
            'api/plugins/models',
          ],
        },
      ],
    },
    apiReferenceSidebar,
    'configuration',
    'troubleshooting',
    'faq',
    'contributing',
  ],
};

export default sidebars;
