window.MkDocsExporter = {

  render: async () => {
    if (window.mermaid) {
      if (typeof window.mermaid.run === 'function') {
        mermaid.initialize({
          startOnLoad: false,
          theme: "base",
          themeVariables: {
              background: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-backgroundColor').trim(),
              lineColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-lineColor').trim(),
              primaryColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-primaryColor').trim(),
              primaryBordColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-primaryBordColor').trim(),
              primaryTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-primaryTextColor').trim(),
              secondaryColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-secondaryColor').trim(),
              secondaryTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-secondaryTextColor').trim(),
              secondaryBordColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-secondaryBordColor').trim(),
              tertiaryColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryColor').trim(),
              tertiaryTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              tertiaryBordColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryBordColor').trim(),
              edgeLabelBackground: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryColor').trim(),
              nodeTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              textColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              titleColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              actorTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              labelColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              labelTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim(),
              loopTextColor: getComputedStyle(document.documentElement.firstChild).getPropertyValue('--md-mermaid-custom-tertiaryTextColor').trim()
            }
        });

        for (const element of document.querySelectorAll('.mermaid > code')) {
          const container = document.createElement('div');

          container.className = 'mermaid';

          await mermaid.run({ nodes: [element] });

          element.parentElement.appendChild(container);
          container.appendChild(element.children[0]);
          element.remove();
        }
      }
    }

  }
};
