import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { IMarkdownParser } from '@jupyterlab/rendermime';
import { ISettingRegistry } from '@jupyterlab/settingregistry';

/**
 * Alert type configuration
 */
interface IAlertConfig {
  className: string;
  title: string;
  iconPath: string;
  iconClass: string;
  iconColor: string;
  iconColorDark: string;
}

const ALERT_TYPES: Record<string, IAlertConfig> = {
  NOTE: {
    className: 'markdown-alert-note',
    title: 'Note',
    iconClass: 'octicon-info',
    iconColor: '#0969da',
    iconColorDark: '#2f81f7',
    iconPath:
      'M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z'
  },
  TIP: {
    className: 'markdown-alert-tip',
    title: 'Tip',
    iconClass: 'octicon-light-bulb',
    iconColor: '#1a7f37',
    iconColorDark: '#3fb950',
    iconPath:
      'M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.848.284.411.537.896.621 1.49a.75.75 0 0 1-1.484.211c-.04-.282-.163-.547-.37-.847a8.456 8.456 0 0 0-.542-.68c-.084-.1-.173-.205-.268-.32C3.201 7.75 2.5 6.766 2.5 5.25 2.5 2.31 4.863 0 8 0s5.5 2.31 5.5 5.25c0 1.516-.701 2.5-1.328 3.259-.095.115-.184.22-.268.319-.207.245-.383.453-.541.681-.208.3-.33.565-.37.847a.751.751 0 0 1-1.485-.212c.084-.593.337-1.078.621-1.489.203-.292.45-.584.673-.848.075-.088.147-.173.213-.253.561-.679.985-1.32.985-2.304 0-2.06-1.637-3.75-4-3.75ZM5.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5ZM6 15.25a.75.75 0 0 1 .75-.75h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1-.75-.75Z'
  },
  IMPORTANT: {
    className: 'markdown-alert-important',
    title: 'Important',
    iconClass: 'octicon-report',
    iconColor: '#8250df',
    iconColorDark: '#a371f7',
    iconPath:
      'M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v9.5A1.75 1.75 0 0 1 14.25 13H8.06l-2.573 2.573A1.458 1.458 0 0 1 3 14.543V13H1.75A1.75 1.75 0 0 1 0 11.25Zm1.75-.25a.25.25 0 0 0-.25.25v9.5c0 .138.112.25.25.25h2a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.5a.25.25 0 0 0 .25-.25v-9.5a.25.25 0 0 0-.25-.25Zm7 2.25v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 9a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z'
  },
  WARNING: {
    className: 'markdown-alert-warning',
    title: 'Warning',
    iconClass: 'octicon-alert',
    iconColor: '#9a6700',
    iconColorDark: '#d29922',
    iconPath:
      'M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z'
  },
  CAUTION: {
    className: 'markdown-alert-caution',
    title: 'Caution',
    iconClass: 'octicon-stop',
    iconColor: '#cf222e',
    iconColorDark: '#f85149',
    iconPath:
      'M4.47.22A.749.749 0 0 1 5 0h6c.199 0 .389.079.53.22l4.25 4.25c.141.14.22.331.22.53v6a.749.749 0 0 1-.22.53l-4.25 4.25A.749.749 0 0 1 11 16H5a.749.749 0 0 1-.53-.22L.22 11.53A.749.749 0 0 1 0 11V5c0-.199.079-.389.22-.53Zm.84 1.28L1.5 5.31v5.38l3.81 3.81h5.38l3.81-3.81V5.31L10.69 1.5ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z'
  }
};

/**
 * Create SVG icon element as data URI with both light and dark theme versions
 */
function createIcon(
  iconPath: string,
  iconClass: string,
  iconColor: string,
  iconColorDark: string
): string {
  // Create light theme icon
  const svgContentLight = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><path fill="${iconColor}" d="${iconPath}"></path></svg>`;
  const dataUriLight = `data:image/svg+xml;base64,${btoa(svgContentLight)}`;

  // Create dark theme icon
  const svgContentDark = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="16" height="16"><path fill="${iconColorDark}" d="${iconPath}"></path></svg>`;
  const dataUriDark = `data:image/svg+xml;base64,${btoa(svgContentDark)}`;

  return (
    `<img src="${dataUriLight}" class="octicon ${iconClass} octicon-light mr-2" width="16" height="16" aria-hidden="true" alt="" />` +
    `<img src="${dataUriDark}" class="octicon ${iconClass} octicon-dark mr-2" width="16" height="16" aria-hidden="true" alt="" />`
  );
}

/**
 * Process markdown text to convert GitHub-style alerts
 */
function processAlerts(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let i = 0;
  let inCodeBlock = false;

  while (i < lines.length) {
    const line = lines[i];

    // Track code blocks (both ``` and ~~~)
    if (line.trim().match(/^```|^~~~/)) {
      inCodeBlock = !inCodeBlock;
      result.push(line);
      i++;
      continue;
    }

    // Skip alert processing inside code blocks
    if (inCodeBlock) {
      result.push(line);
      i++;
      continue;
    }

    const alertMatch = line.match(
      /^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$/
    );

    if (alertMatch) {
      const alertType = alertMatch[1];
      const contentLines: string[] = [];

      i++;
      while (i < lines.length && lines[i].startsWith('>')) {
        const content = lines[i].replace(/^>\s?/, '');
        if (content) {
          contentLines.push(content);
        }
        i++;
      }

      if (contentLines.length > 0) {
        const content = contentLines.join('\n\n');

        // Use HTML comments as markers that will survive markdown processing
        result.push(
          `<!--ALERT_START:${alertType}-->`,
          content,
          `<!--ALERT_END:${alertType}-->`
        );
        continue;
      }
    }

    result.push(line);
    i++;
  }

  return result.join('\n');
}

/**
 * Post-process rendered HTML to wrap alert markers with styled divs
 */
function postProcessAlerts(html: string, showBackgrounds: boolean): string {
  // Replace alert markers with proper HTML structure
  const result = html.replace(
    /<!--ALERT_START:(NOTE|TIP|IMPORTANT|WARNING|CAUTION)-->([\s\S]*?)<!--ALERT_END:\1-->/g,
    (match, alertType, content) => {
      const config = ALERT_TYPES[alertType];
      const icon = createIcon(
        config.iconPath,
        config.iconClass,
        config.iconColor,
        config.iconColorDark
      );
      const backgroundClass = showBackgrounds
        ? ' markdown-alert-with-backgrounds'
        : '';

      return (
        `<div class="markdown-alert ${config.className}${backgroundClass}" dir="auto">` +
        `<p class="markdown-alert-title" dir="auto">${icon}${config.title}</p>` +
        content +
        `</div>`
      );
    }
  );
  return result;
}

/**
 * Initialization data for the jupyterlab_github_markdown_alerts_extension extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'jupyterlab_github_markdown_alerts_extension:plugin',
  description:
    'Jupyterlab extension to render alerts tips like they are rendered in github in markdown',
  autoStart: true,
  requires: [IMarkdownParser],
  optional: [ISettingRegistry],
  activate: (
    app: JupyterFrontEnd,
    markdownParser: IMarkdownParser,
    settingRegistry: ISettingRegistry | null
  ) => {
    let showBackgrounds = false;

    // Load settings
    if (settingRegistry) {
      const loadSettings = () => {
        settingRegistry
          .load(plugin.id)
          .then(settings => {
            showBackgrounds = settings.get('showBackgrounds')
              .composite as boolean;
            settings.changed.connect(() => {
              showBackgrounds = settings.get('showBackgrounds')
                .composite as boolean;
            });
          })
          .catch(reason => {
            console.error(
              'Failed to load settings for jupyterlab_github_markdown_alerts_extension',
              reason
            );
          });
      };
      loadSettings();
    }

    const originalRender = markdownParser.render.bind(markdownParser);

    markdownParser.render = async (content: string): Promise<string> => {
      const processedContent = processAlerts(content);
      const renderedHtml = await originalRender(processedContent);
      return postProcessAlerts(renderedHtml, showBackgrounds);
    };

    console.log(
      'JupyterLab extension jupyterlab_github_markdown_alerts_extension is activated!'
    );
  }
};

export default plugin;
