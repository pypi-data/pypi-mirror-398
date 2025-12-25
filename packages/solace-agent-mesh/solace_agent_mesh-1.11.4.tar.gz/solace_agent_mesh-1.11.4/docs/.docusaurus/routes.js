import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/solace-agent-mesh/docs',
    component: ComponentCreator('/solace-agent-mesh/docs', '15d'),
    routes: [
      {
        path: '/solace-agent-mesh/docs',
        component: ComponentCreator('/solace-agent-mesh/docs', 'aba'),
        routes: [
          {
            path: '/solace-agent-mesh/docs',
            component: ComponentCreator('/solace-agent-mesh/docs', '827'),
            routes: [
              {
                path: '/solace-agent-mesh/docs/documentation/components/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/', 'e92'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/agents',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/agents', 'c73'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/builtin-tools/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/builtin-tools/', 'd13'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/builtin-tools/artifact-management',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/builtin-tools/artifact-management', '537'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/builtin-tools/audio-tools',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/builtin-tools/audio-tools', '0f0'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/builtin-tools/data-analysis-tools',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/builtin-tools/data-analysis-tools', '7b8'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/builtin-tools/embeds',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/builtin-tools/embeds', 'cdc'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/cli',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/cli', 'e08'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/gateways',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/gateways', 'c3d'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/orchestrator',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/orchestrator', '065'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/platform-service',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/platform-service', '874'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/plugins',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/plugins', '8f0'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/projects',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/projects', '7be'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/prompts',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/prompts', 'd87'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/proxies',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/proxies', 'bf5'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/components/speech',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/components/speech', 'b27'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/', '392'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/debugging',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/debugging', '39b'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/deployment-options',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/deployment-options', '091'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/kubernetes/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/kubernetes/', 'c3e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/kubernetes/kubernetes-deployment-guide',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/kubernetes/kubernetes-deployment-guide', 'a9b'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/logging',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/logging', 'd9a'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/observability',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/observability', 'a35'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/deploying/proxy_configuration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/deploying/proxy_configuration', 'efc'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/', 'c3b'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/create-agents',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/create-agents', 'cbd'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/create-gateways',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/create-gateways', '328'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/creating-python-tools',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/creating-python-tools', '0de'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/creating-service-providers',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/creating-service-providers', 'b29'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/evaluations',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/evaluations', '227'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/structure',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/structure', 'c81'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/bedrock-agents',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/bedrock-agents', '84e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/custom-agent',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/custom-agent', '52b'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/event-mesh-gateway',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/event-mesh-gateway', '84e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/mcp-integration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/mcp-integration', 'ccd'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/mongodb-integration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/mongodb-integration', '7fe'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/rag-integration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/rag-integration', '374'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/rest-gateway',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/rest-gateway', 'b04'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/slack-integration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/slack-integration', '82e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/sql-database',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/sql-database', '88e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/developing/tutorials/teams-integration',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/developing/tutorials/teams-integration', '5ce'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/', 'c16'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/agent-builder',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/agent-builder', 'ee2'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/connectors/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/connectors/', 'f63'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/installation',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/installation', '1d0'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/openapi-tools',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/openapi-tools', '165'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/rbac-setup-guide',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/rbac-setup-guide', 'd3d'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/secure-user-delegated-access',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/secure-user-delegated-access', '7f7'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/single-sign-on',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/single-sign-on', '12a'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/enterprise/wheel-installation',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/enterprise/wheel-installation', '87f'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/getting-started/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/getting-started/', 'c22'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/getting-started/architecture',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/getting-started/architecture', 'd19'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/getting-started/introduction',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/getting-started/introduction', 'f14'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/getting-started/try-agent-mesh',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/getting-started/try-agent-mesh', '41f'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/', 'c1e'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/artifact-storage',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/artifact-storage', '1f1'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/configurations',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/configurations', 'ae2'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/installation',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/installation', '466'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/large_language_models',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/large_language_models', '185'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/run-project',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/run-project', '078'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/session-storage',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/session-storage', '9b4'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/installing-and-configuring/user-feedback',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/installing-and-configuring/user-feedback', '711'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/migrations/a2a-upgrade/a2a-gateway-upgrade-to-0.3.0',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/migrations/a2a-upgrade/a2a-gateway-upgrade-to-0.3.0', '1b5'),
                exact: true,
                sidebar: "docSidebar"
              },
              {
                path: '/solace-agent-mesh/docs/documentation/migrations/a2a-upgrade/a2a-technical-migration-map',
                component: ComponentCreator('/solace-agent-mesh/docs/documentation/migrations/a2a-upgrade/a2a-technical-migration-map', 'aa7'),
                exact: true,
                sidebar: "docSidebar"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
