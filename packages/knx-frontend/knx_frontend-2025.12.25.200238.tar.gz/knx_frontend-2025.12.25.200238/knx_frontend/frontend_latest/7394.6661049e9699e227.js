export const __webpack_id__="7394";export const __webpack_ids__=["7394"];export const __webpack_modules__={61974:function(e,t,o){var i={"./ha-icon-prev":["48268","2477"],"./ha-icon-button-toolbar":["48939","3736"],"./ha-alert":["17963"],"./ha-icon-button-toggle":["35150","2851"],"./ha-svg-icon.ts":["60961"],"./ha-alert.ts":["17963"],"./ha-icon":["22598"],"./ha-icon-next.ts":["28608"],"./ha-qr-code.ts":["16618","1343","6247"],"./ha-icon-overflow-menu.ts":["53623","2016","7644"],"./ha-icon-button-toggle.ts":["35150","2851"],"./ha-icon-button-group":["39651","7760"],"./ha-svg-icon":["60961"],"./ha-icon-button-prev":["80263","8076"],"./ha-icon-button.ts":["60733"],"./ha-icon-overflow-menu":["53623","2016","7644"],"./ha-icon-button-arrow-next":["56231","5500"],"./ha-icon-button-prev.ts":["80263","8076"],"./ha-icon-picker":["88867","624"],"./ha-icon-button-toolbar.ts":["48939","3736"],"./ha-icon-button-arrow-prev.ts":["371"],"./ha-icon-button-next":["29795","9488"],"./ha-icon-next":["28608"],"./ha-icon-picker.ts":["88867","624"],"./ha-icon-prev.ts":["48268","2477"],"./ha-icon-button-arrow-prev":["371"],"./ha-icon-button-next.ts":["29795","9488"],"./ha-icon.ts":["22598"],"./ha-qr-code":["16618","1343","6247"],"./ha-icon-button":["60733"],"./ha-icon-button-group.ts":["39651","7760"],"./ha-icon-button-arrow-next.ts":["56231","5500"]};function a(e){if(!o.o(i,e))return Promise.resolve().then((function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}));var t=i[e],a=t[0];return Promise.all(t.slice(1).map(o.e)).then((function(){return o(a)}))}a.keys=()=>Object.keys(i),a.id=61974,e.exports=a},25115:function(e,t,o){var i={"./flow-preview-generic.ts":["66633","3806","4916","5633","1045","1794"],"./flow-preview-template":["71996","3806","4916","5633","1045","9149"],"./flow-preview-generic_camera":["93143","3806","4916","5633","1045","1628"],"./flow-preview-generic_camera.ts":["93143","3806","4916","5633","1045","1628"],"./flow-preview-generic":["66633","3806","4916","5633","1045","1794"],"./flow-preview-template.ts":["71996","3806","4916","5633","1045","9149"]};function a(e){if(!o.o(i,e))return Promise.resolve().then((function(){var t=new Error("Cannot find module '"+e+"'");throw t.code="MODULE_NOT_FOUND",t}));var t=i[e],a=t[0];return Promise.all(t.slice(1).map(o.e)).then((function(){return o(a)}))}a.keys=()=>Object.keys(i),a.id=25115,e.exports=a},45817:function(e,t,o){o.d(t,{d:()=>i});const i=(e,t=!0)=>{if(e.defaultPrevented||0!==e.button||e.metaKey||e.ctrlKey||e.shiftKey)return;const o=e.composedPath().find((e=>"A"===e.tagName));if(!o||o.target||o.hasAttribute("download")||"external"===o.getAttribute("rel"))return;let i=o.href;if(!i||-1!==i.indexOf("mailto:"))return;const a=window.location,s=a.origin||a.protocol+"//"+a.host;return i.startsWith(s)&&(i=i.slice(s.length),"#"!==i)?(t&&e.preventDefault(),i):void 0}},48565:function(e,t,o){o.d(t,{d:()=>i});const i=e=>{switch(e.language){case"cs":case"de":case"fi":case"fr":case"sk":case"sv":return" ";default:return""}}},86451:function(e,t,o){var i=o(62826),a=o(96196),s=o(77845);class n extends a.WF{render(){const e=a.qy`<div class="header-title">
      <slot name="title"></slot>
    </div>`,t=a.qy`<div class="header-subtitle">
      <slot name="subtitle"></slot>
    </div>`;return a.qy`
      <header class="header">
        <div class="header-bar">
          <section class="header-navigation-icon">
            <slot name="navigationIcon"></slot>
          </section>
          <section class="header-content">
            ${"above"===this.subtitlePosition?a.qy`${t}${e}`:a.qy`${e}${t}`}
          </section>
          <section class="header-action-items">
            <slot name="actionItems"></slot>
          </section>
        </div>
        <slot></slot>
      </header>
    `}static get styles(){return[a.AH`
        :host {
          display: block;
        }
        :host([show-border]) {
          border-bottom: 1px solid
            var(--mdc-dialog-scroll-divider-color, rgba(0, 0, 0, 0.12));
        }
        .header-bar {
          display: flex;
          flex-direction: row;
          align-items: center;
          padding: 0 var(--ha-space-1);
          box-sizing: border-box;
        }
        .header-content {
          flex: 1;
          padding: 10px var(--ha-space-1);
          display: flex;
          flex-direction: column;
          justify-content: center;
          min-height: var(--ha-space-12);
          min-width: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .header-title {
          height: var(
            --ha-dialog-header-title-height,
            calc(var(--ha-font-size-xl) + var(--ha-space-1))
          );
          font-size: var(--ha-font-size-xl);
          line-height: var(--ha-line-height-condensed);
          font-weight: var(--ha-font-weight-medium);
          color: var(--ha-dialog-header-title-color, var(--primary-text-color));
        }
        .header-subtitle {
          font-size: var(--ha-font-size-m);
          line-height: var(--ha-line-height-normal);
          color: var(
            --ha-dialog-header-subtitle-color,
            var(--secondary-text-color)
          );
        }
        @media all and (min-width: 450px) and (min-height: 500px) {
          .header-bar {
            padding: 0 var(--ha-space-2);
          }
        }
        .header-navigation-icon {
          flex: none;
          min-width: var(--ha-space-2);
          height: 100%;
          display: flex;
          flex-direction: row;
        }
        .header-action-items {
          flex: none;
          min-width: var(--ha-space-2);
          height: 100%;
          display: flex;
          flex-direction: row;
        }
      `]}constructor(...e){super(...e),this.subtitlePosition="below",this.showBorder=!1}}(0,i.__decorate)([(0,s.MZ)({type:String,attribute:"subtitle-position"})],n.prototype,"subtitlePosition",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean,reflect:!0,attribute:"show-border"})],n.prototype,"showBorder",void 0),n=(0,i.__decorate)([(0,s.EM)("ha-dialog-header")],n)},23442:function(e,t,o){o.d(t,{$:()=>i});const i=e=>{const t={};return e.forEach((e=>{if(void 0!==e.description?.suggested_value&&null!==e.description?.suggested_value)t[e.name]=e.description.suggested_value;else if("default"in e)t[e.name]=e.default;else if("expandable"===e.type){const o=i(e.schema);(e.required||Object.keys(o).length)&&(t[e.name]=o)}else if(e.required){if("boolean"===e.type)t[e.name]=!1;else if("string"===e.type)t[e.name]="";else if("integer"===e.type)t[e.name]="valueMin"in e?e.valueMin:0;else if("constant"===e.type)t[e.name]=e.value;else if("float"===e.type)t[e.name]=0;else if("select"===e.type){if(e.options.length){const o=e.options[0];t[e.name]=Array.isArray(o)?o[0]:o}}else if("positive_time_period_dict"===e.type)t[e.name]={hours:0,minutes:0,seconds:0};else if("selector"in e){const o=e.selector;if("device"in o)t[e.name]=o.device?.multiple?[]:"";else if("entity"in o)t[e.name]=o.entity?.multiple?[]:"";else if("area"in o)t[e.name]=o.area?.multiple?[]:"";else if("label"in o)t[e.name]=o.label?.multiple?[]:"";else if("boolean"in o)t[e.name]=!1;else if("addon"in o||"attribute"in o||"file"in o||"icon"in o||"template"in o||"text"in o||"theme"in o||"object"in o)t[e.name]="";else if("number"in o)t[e.name]=o.number?.min??0;else if("select"in o){if(o.select?.options.length){const i=o.select.options[0],a="string"==typeof i?i:i.value;t[e.name]=o.select.multiple?[a]:a}}else if("country"in o)o.country?.countries?.length&&(t[e.name]=o.country.countries[0]);else if("language"in o)o.language?.languages?.length&&(t[e.name]=o.language.languages[0]);else if("duration"in o)t[e.name]={hours:0,minutes:0,seconds:0};else if("time"in o)t[e.name]="00:00:00";else if("date"in o||"datetime"in o){const o=(new Date).toISOString().slice(0,10);t[e.name]=`${o}T00:00:00`}else if("color_rgb"in o)t[e.name]=[0,0,0];else if("color_temp"in o)t[e.name]=o.color_temp?.min_mireds??153;else if("action"in o||"trigger"in o||"condition"in o)t[e.name]=[];else if("media"in o||"target"in o)t[e.name]={};else{if(!("state"in o))throw new Error(`Selector ${Object.keys(o)[0]} not supported in initial form data`);t[e.name]=o.state?.multiple?[]:""}}}else;})),t}},91120:function(e,t,o){var i=o(62826),a=o(96196),s=o(77845),n=o(51757),r=o(92542);o(17963),o(87156);const l={boolean:()=>o.e("2018").then(o.bind(o,49337)),constant:()=>o.e("9938").then(o.bind(o,37449)),float:()=>o.e("812").then(o.bind(o,5863)),grid:()=>o.e("798").then(o.bind(o,81213)),expandable:()=>o.e("8550").then(o.bind(o,29989)),integer:()=>o.e("1364").then(o.bind(o,28175)),multi_select:()=>Promise.all([o.e("2016"),o.e("3616")]).then(o.bind(o,59827)),positive_time_period_dict:()=>o.e("5846").then(o.bind(o,19797)),select:()=>o.e("6262").then(o.bind(o,29317)),string:()=>o.e("8389").then(o.bind(o,33092)),optional_actions:()=>o.e("1454").then(o.bind(o,2173))},c=(e,t)=>e?!t.name||t.flatten?e:e[t.name]:null;class d extends a.WF{getFormProperties(){return{}}async focus(){await this.updateComplete;const e=this.renderRoot.querySelector(".root");if(e)for(const t of e.children)if("HA-ALERT"!==t.tagName){t instanceof a.mN&&await t.updateComplete,t.focus();break}}willUpdate(e){e.has("schema")&&this.schema&&this.schema.forEach((e=>{"selector"in e||l[e.type]?.()}))}render(){return a.qy`
      <div class="root" part="root">
        ${this.error&&this.error.base?a.qy`
              <ha-alert alert-type="error">
                ${this._computeError(this.error.base,this.schema)}
              </ha-alert>
            `:""}
        ${this.schema.map((e=>{const t=((e,t)=>e&&t.name?e[t.name]:null)(this.error,e),o=((e,t)=>e&&t.name?e[t.name]:null)(this.warning,e);return a.qy`
            ${t?a.qy`
                  <ha-alert own-margin alert-type="error">
                    ${this._computeError(t,e)}
                  </ha-alert>
                `:o?a.qy`
                    <ha-alert own-margin alert-type="warning">
                      ${this._computeWarning(o,e)}
                    </ha-alert>
                  `:""}
            ${"selector"in e?a.qy`<ha-selector
                  .schema=${e}
                  .hass=${this.hass}
                  .narrow=${this.narrow}
                  .name=${e.name}
                  .selector=${e.selector}
                  .value=${c(this.data,e)}
                  .label=${this._computeLabel(e,this.data)}
                  .disabled=${e.disabled||this.disabled||!1}
                  .placeholder=${e.required?void 0:e.default}
                  .helper=${this._computeHelper(e)}
                  .localizeValue=${this.localizeValue}
                  .required=${e.required||!1}
                  .context=${this._generateContext(e)}
                ></ha-selector>`:(0,n._)(this.fieldElementName(e.type),{schema:e,data:c(this.data,e),label:this._computeLabel(e,this.data),helper:this._computeHelper(e),disabled:this.disabled||e.disabled||!1,hass:this.hass,localize:this.hass?.localize,computeLabel:this.computeLabel,computeHelper:this.computeHelper,localizeValue:this.localizeValue,context:this._generateContext(e),...this.getFormProperties()})}
          `}))}
      </div>
    `}fieldElementName(e){return`ha-form-${e}`}_generateContext(e){if(!e.context)return;const t={};for(const[o,i]of Object.entries(e.context))t[o]=this.data[i];return t}createRenderRoot(){const e=super.createRenderRoot();return this.addValueChangedListener(e),e}addValueChangedListener(e){e.addEventListener("value-changed",(e=>{e.stopPropagation();const t=e.target.schema;if(e.target===this)return;const o=!t.name||"flatten"in t&&t.flatten?e.detail.value:{[t.name]:e.detail.value};this.data={...this.data,...o},(0,r.r)(this,"value-changed",{value:this.data})}))}_computeLabel(e,t){return this.computeLabel?this.computeLabel(e,t):e?e.name:""}_computeHelper(e){return this.computeHelper?this.computeHelper(e):""}_computeError(e,t){return Array.isArray(e)?a.qy`<ul>
        ${e.map((e=>a.qy`<li>
              ${this.computeError?this.computeError(e,t):e}
            </li>`))}
      </ul>`:this.computeError?this.computeError(e,t):e}_computeWarning(e,t){return this.computeWarning?this.computeWarning(e,t):e}constructor(...e){super(...e),this.narrow=!1,this.disabled=!1}}d.shadowRootOptions={mode:"open",delegatesFocus:!0},d.styles=a.AH`
    .root > * {
      display: block;
    }
    .root > *:not([own-margin]):not(:last-child) {
      margin-bottom: 24px;
    }
    ha-alert[own-margin] {
      margin-bottom: 4px;
    }
  `,(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],d.prototype,"narrow",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"data",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"schema",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"error",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"warning",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],d.prototype,"disabled",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"computeError",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"computeWarning",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"computeLabel",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"computeHelper",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],d.prototype,"localizeValue",void 0),d=(0,i.__decorate)([(0,s.EM)("ha-form")],d)},28089:function(e,t,o){var i=o(62826),a=o(96196),s=o(77845),n=o(1420),r=o(30015),l=o.n(r),c=o(92542),d=o(2209);let p;const h=e=>a.qy`${e}`,m=new class{get(e){return this._cache.get(e)}set(e,t){this._cache.set(e,t),this._expiration&&window.setTimeout((()=>this._cache.delete(e)),this._expiration)}has(e){return this._cache.has(e)}constructor(e){this._cache=new Map,this._expiration=e}}(1e3),_={reType:/(?<input>(\[!(?<type>caution|important|note|tip|warning)\])(?:\s|\\n)?)/i,typeToHaAlert:{caution:"error",important:"info",note:"info",tip:"success",warning:"warning"}};class u extends a.mN{disconnectedCallback(){if(super.disconnectedCallback(),this.cache){const e=this._computeCacheKey();m.set(e,this.innerHTML)}}createRenderRoot(){return this}update(e){super.update(e),void 0!==this.content&&(this._renderPromise=this._render())}async getUpdateComplete(){return await super.getUpdateComplete(),await this._renderPromise,!0}willUpdate(e){if(!this.innerHTML&&this.cache){const e=this._computeCacheKey();m.has(e)&&((0,a.XX)(h((0,n._)(m.get(e))),this.renderRoot),this._resize())}}_computeCacheKey(){return l()({content:this.content,allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl,breaks:this.breaks})}async _render(){const e=await(async(e,t,i)=>(p||(p=(0,d.LV)(new Worker(new URL(o.p+o.u("5640"),o.b)))),p.renderMarkdown(e,t,i)))(String(this.content),{breaks:this.breaks,gfm:!0},{allowSvg:this.allowSvg,allowDataUrl:this.allowDataUrl});(0,a.XX)(h((0,n._)(e.join(""))),this.renderRoot),this._resize();const t=document.createTreeWalker(this,NodeFilter.SHOW_ELEMENT,null);for(;t.nextNode();){const e=t.currentNode;if(e instanceof HTMLAnchorElement&&e.host!==document.location.host)e.target="_blank",e.rel="noreferrer noopener";else if(e instanceof HTMLImageElement)this.lazyImages&&(e.loading="lazy"),e.addEventListener("load",this._resize);else if(e instanceof HTMLQuoteElement){const o=e.firstElementChild?.firstChild?.textContent&&_.reType.exec(e.firstElementChild.firstChild.textContent);if(o){const{type:i}=o.groups,a=document.createElement("ha-alert");a.alertType=_.typeToHaAlert[i.toLowerCase()],a.append(...Array.from(e.childNodes).map((e=>{const t=Array.from(e.childNodes);if(!this.breaks&&t.length){const e=t[0];e.nodeType===Node.TEXT_NODE&&e.textContent===o.input&&e.textContent?.includes("\n")&&(e.textContent=e.textContent.split("\n").slice(1).join("\n"))}return t})).reduce(((e,t)=>e.concat(t)),[]).filter((e=>e.textContent&&e.textContent!==o.input))),t.parentNode().replaceChild(a,e)}}else e instanceof HTMLElement&&["ha-alert","ha-qr-code","ha-icon","ha-svg-icon"].includes(e.localName)&&o(61974)(`./${e.localName}`)}}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1,this._renderPromise=Promise.resolve(),this._resize=()=>(0,c.r)(this,"content-resize")}}(0,i.__decorate)([(0,s.MZ)()],u.prototype,"content",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:"allow-svg",type:Boolean})],u.prototype,"allowSvg",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:"allow-data-url",type:Boolean})],u.prototype,"allowDataUrl",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"breaks",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean,attribute:"lazy-images"})],u.prototype,"lazyImages",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],u.prototype,"cache",void 0),u=(0,i.__decorate)([(0,s.EM)("ha-markdown-element")],u);class g extends a.WF{async getUpdateComplete(){const e=await super.getUpdateComplete();return await(this._markdownElement?.updateComplete),e}render(){return this.content?a.qy`<ha-markdown-element
      .content=${this.content}
      .allowSvg=${this.allowSvg}
      .allowDataUrl=${this.allowDataUrl}
      .breaks=${this.breaks}
      .lazyImages=${this.lazyImages}
      .cache=${this.cache}
    ></ha-markdown-element>`:a.s6}constructor(...e){super(...e),this.allowSvg=!1,this.allowDataUrl=!1,this.breaks=!1,this.lazyImages=!1,this.cache=!1}}g.styles=a.AH`
    :host {
      display: block;
    }
    ha-markdown-element {
      -ms-user-select: text;
      -webkit-user-select: text;
      -moz-user-select: text;
    }
    ha-markdown-element > *:first-child {
      margin-top: 0;
    }
    ha-markdown-element > *:last-child {
      margin-bottom: 0;
    }
    ha-alert {
      display: block;
      margin: var(--ha-space-1) 0;
    }
    a {
      color: var(--markdown-link-color, var(--primary-color));
    }
    img {
      background-color: var(--markdown-image-background-color);
      border-radius: var(--markdown-image-border-radius);
      max-width: 100%;
      height: auto;
      width: auto;
      transition: height 0.2s ease-in-out;
    }
    p:first-child > img:first-child {
      vertical-align: top;
    }
    p:first-child > img:last-child {
      vertical-align: top;
    }
    :host > ul,
    :host > ol {
      padding-inline-start: var(--markdown-list-indent, revert);
    }
    li {
      &:has(input[type="checkbox"]) {
        list-style: none;
        & > input[type="checkbox"] {
          margin-left: 0;
        }
      }
    }
    svg {
      background-color: var(--markdown-svg-background-color, none);
      color: var(--markdown-svg-color, none);
    }
    code,
    pre {
      background-color: var(--markdown-code-background-color, none);
      border-radius: var(--ha-border-radius-sm);
      color: var(--markdown-code-text-color, inherit);
    }
    code {
      font-size: var(--ha-font-size-s);
      padding: 0.2em 0.4em;
    }
    pre code {
      padding: 0;
    }
    pre {
      padding: var(--ha-space-4);
      overflow: auto;
      line-height: var(--ha-line-height-condensed);
      font-family: var(--ha-font-family-code);
    }
    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      line-height: initial;
    }
    h2 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-bold);
    }
    hr {
      border-color: var(--divider-color);
      border-bottom: none;
      margin: var(--ha-space-4) 0;
    }
    table {
      border-collapse: var(--markdown-table-border-collapse, collapse);
    }
    div:has(> table) {
      overflow: auto;
    }
    th {
      text-align: start;
    }
    td,
    th {
      border-width: var(--markdown-table-border-width, 1px);
      border-style: var(--markdown-table-border-style, solid);
      border-color: var(--markdown-table-border-color, var(--divider-color));
      padding: 0.25em 0.5em;
    }
    blockquote {
      border-left: 4px solid var(--divider-color);
      margin-inline: 0;
      padding-inline: 1em;
    }
  `,(0,i.__decorate)([(0,s.MZ)()],g.prototype,"content",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:"allow-svg",type:Boolean})],g.prototype,"allowSvg",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:"allow-data-url",type:Boolean})],g.prototype,"allowDataUrl",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],g.prototype,"breaks",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean,attribute:"lazy-images"})],g.prototype,"lazyImages",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],g.prototype,"cache",void 0),(0,i.__decorate)([(0,s.P)("ha-markdown-element")],g.prototype,"_markdownElement",void 0),g=(0,i.__decorate)([(0,s.EM)("ha-markdown")],g)},64109:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(65686),s=o(96196),n=o(77845),r=e([a]);a=(r.then?(await r)():r)[0];class l extends a.A{updated(e){if(super.updated(e),e.has("size"))switch(this.size){case"tiny":this.style.setProperty("--ha-progress-ring-size","16px");break;case"small":this.style.setProperty("--ha-progress-ring-size","28px");break;case"medium":this.style.setProperty("--ha-progress-ring-size","48px");break;case"large":this.style.setProperty("--ha-progress-ring-size","68px");break;case void 0:this.style.removeProperty("--ha-progress-ring-size")}}static get styles(){return[a.A.styles,s.AH`
        :host {
          --indicator-color: var(
            --ha-progress-ring-indicator-color,
            var(--primary-color)
          );
          --track-color: var(
            --ha-progress-ring-divider-color,
            var(--divider-color)
          );
          --track-width: 4px;
          --speed: 3.5s;
          --size: var(--ha-progress-ring-size, 48px);
        }
      `]}}(0,i.__decorate)([(0,n.MZ)()],l.prototype,"size",void 0),l=(0,i.__decorate)([(0,n.EM)("ha-progress-ring")],l),t()}catch(l){t(l)}}))},41558:function(e,t,o){o.d(t,{KC:()=>d,Vy:()=>l,ds:()=>s,ew:()=>r,g5:()=>c,tl:()=>n});var i=o(9477),a=o(31136);const s=(e,t,o)=>e.connection.subscribeMessage(o,{type:"assist_satellite/intercept_wake_word",entity_id:t}),n=(e,t)=>e.callWS({type:"assist_satellite/test_connection",entity_id:t}),r=(e,t,o)=>e.callService("assist_satellite","announce",o,{entity_id:t}),l=(e,t)=>e.callWS({type:"assist_satellite/get_configuration",entity_id:t}),c=(e,t,o)=>e.callWS({type:"assist_satellite/set_wake_words",entity_id:t,wake_word_ids:o}),d=e=>e&&e.state!==a.Hh&&(0,i.$)(e,1)},54193:function(e,t,o){o.d(t,{Hg:()=>i,e0:()=>a});const i=e=>e.map((e=>{if("string"!==e.type)return e;switch(e.name){case"username":return{...e,autocomplete:"username",autofocus:!0};case"password":return{...e,autocomplete:"current-password"};case"code":return{...e,autocomplete:"one-time-code",autofocus:!0};default:return e}})),a=(e,t)=>e.callWS({type:"auth/sign_path",path:t})},23608:function(e,t,o){o.d(t,{PN:()=>s,jm:()=>n,sR:()=>r,t1:()=>a,t2:()=>c,yu:()=>l});const i={"HA-Frontend-Base":`${location.protocol}//${location.host}`},a=(e,t,o)=>e.callApi("POST","config/config_entries/flow",{handler:t,show_advanced_options:Boolean(e.userData?.showAdvanced),entry_id:o},i),s=(e,t)=>e.callApi("GET",`config/config_entries/flow/${t}`,void 0,i),n=(e,t,o)=>e.callApi("POST",`config/config_entries/flow/${t}`,o,i),r=(e,t)=>e.callApi("DELETE",`config/config_entries/flow/${t}`),l=(e,t)=>e.callApi("GET","config/config_entries/flow_handlers"+(t?`?type=${t}`:"")),c=e=>e.sendMessagePromise({type:"config_entries/flow/progress"})},86807:function(e,t,o){o.d(t,{K:()=>a,P:()=>i});const i=(e,t)=>e.subscribeEvents(t,"data_entry_flow_progressed"),a=(e,t)=>e.subscribeEvents(t,"data_entry_flow_progress_update")},31136:function(e,t,o){o.d(t,{HV:()=>s,Hh:()=>a,KF:()=>r,ON:()=>n,g0:()=>d,s7:()=>l});var i=o(99245);const a="unavailable",s="unknown",n="on",r="off",l=[a,s],c=[a,s,r],d=(0,i.g)(l);(0,i.g)(c)},73103:function(e,t,o){o.d(t,{F:()=>s,Q:()=>a});const i=["generic_camera","template"],a=(e,t,o,i,a,s)=>e.connection.subscribeMessage(s,{type:`${t}/start_preview`,flow_id:o,flow_type:i,user_input:a}),s=e=>i.includes(e)?e:"generic"},90313:function(e,t,o){o.a(e,(async function(e,i){try{o.r(t);var a=o(62826),s=o(96196),n=o(77845),r=o(22786),l=o(92542),c=(o(95637),o(86451),o(60733),o(86807)),d=o(39396),p=o(62001),h=o(10234),m=o(93056),_=o(64533),u=o(12083),g=o(84398),f=o(19486),w=(o(59395),o(12527)),v=o(35804),y=o(53264),b=o(73042),$=e([m,_,u,g,f,w]);[m,_,u,g,f,w]=$.then?(await $)():$;const k="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",x="M15.07,11.25L14.17,12.17C13.45,12.89 13,13.5 13,15H11V14.5C11,13.39 11.45,12.39 12.17,11.67L13.41,10.41C13.78,10.05 14,9.55 14,9C14,7.89 13.1,7 12,7A2,2 0 0,0 10,9H8A4,4 0 0,1 12,5A4,4 0 0,1 16,9C16,9.88 15.64,10.67 15.07,11.25M13,19H11V17H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12C22,6.47 17.5,2 12,2Z";let z=0;class C extends s.WF{async showDialog(e){this._params=e,this._instance=z++;const t=this._instance;let o;if(e.startFlowHandler){this._loading="loading_flow",this._handler=e.startFlowHandler;try{o=await this._params.flowConfig.createFlow(this.hass,e.startFlowHandler)}catch(i){this.closeDialog();let e=i.message||i.body||"Unknown error";return"string"!=typeof e&&(e=JSON.stringify(e)),void(0,h.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:`${this.hass.localize("ui.panel.config.integrations.config_flow.could_not_load")}: ${e}`})}if(t!==this._instance)return}else{if(!e.continueFlowId)return;this._loading="loading_flow";try{o=await e.flowConfig.fetchFlow(this.hass,e.continueFlowId)}catch(i){this.closeDialog();let e=i.message||i.body||"Unknown error";return"string"!=typeof e&&(e=JSON.stringify(e)),void(0,h.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:`${this.hass.localize("ui.panel.config.integrations.config_flow.could_not_load")}: ${e}`})}}t===this._instance&&(this._processStep(o),this._loading=void 0)}closeDialog(){if(!this._params)return;const e=Boolean(this._step&&["create_entry","abort"].includes(this._step.type));!this._step||e||this._params.continueFlowId||this._params.flowConfig.deleteFlow(this.hass,this._step.flow_id),this._step&&this._params.dialogClosedCallback&&this._params.dialogClosedCallback({flowFinished:e,entryId:"result"in this._step?this._step.result?.entry_id:void 0}),this._loading=void 0,this._step=void 0,this._params=void 0,this._handler=void 0,this._unsubDataEntryFlowProgress&&(this._unsubDataEntryFlowProgress(),this._unsubDataEntryFlowProgress=void 0),(0,l.r)(this,"dialog-closed",{dialog:this.localName})}_getDialogTitle(){if(this._loading||!this._step||!this._params)return"";switch(this._step.type){case"form":return this._params.flowConfig.renderShowFormStepHeader(this.hass,this._step);case"abort":return this._params.flowConfig.renderAbortHeader?this._params.flowConfig.renderAbortHeader(this.hass,this._step):this.hass.localize(`component.${this._params.domain??this._step.handler}.title`);case"progress":return this._params.flowConfig.renderShowFormProgressHeader(this.hass,this._step);case"menu":return this._params.flowConfig.renderMenuHeader(this.hass,this._step);case"create_entry":{const e=this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),this._step.result?.entry_id,this._params.carryOverDevices).length;return this.hass.localize("ui.panel.config.integrations.config_flow."+(e?"device_created":"success"),{number:e})}default:return""}}_getDialogSubtitle(){if(this._loading||!this._step||!this._params)return"";switch(this._step.type){case"form":return this._params.flowConfig.renderShowFormStepSubheader?.(this.hass,this._step);case"abort":return this._params.flowConfig.renderAbortSubheader?.(this.hass,this._step);case"progress":return this._params.flowConfig.renderShowFormProgressSubheader?.(this.hass,this._step);case"menu":return this._params.flowConfig.renderMenuSubheader?.(this.hass,this._step);default:return""}}render(){if(!this._params)return s.s6;const e=["form","menu","external","progress","data_entry_flow_progressed"].includes(this._step?.type)&&this._params.manifest?.is_built_in||!!this._params.manifest?.documentation,t=this._getDialogTitle(),o=this._getDialogSubtitle();return s.qy`
      <ha-dialog
        open
        @closed=${this.closeDialog}
        scrimClickAction
        escapeKeyAction
        hideActions
        .heading=${t||!0}
      >
        <ha-dialog-header slot="heading">
          <ha-icon-button
            .label=${this.hass.localize("ui.common.close")}
            .path=${k}
            dialogAction="close"
            slot="navigationIcon"
          ></ha-icon-button>

          <div
            slot="title"
            class="dialog-title${"form"===this._step?.type?" form":""}"
            title=${t}
          >
            ${t}
          </div>

          ${o?s.qy` <div slot="subtitle">${o}</div>`:s.s6}
          ${e&&!this._loading&&this._step?s.qy`
                <a
                  slot="actionItems"
                  class="help"
                  href=${this._params.manifest.is_built_in?(0,p.o)(this.hass,`/integrations/${this._params.manifest.domain}`):this._params.manifest.documentation}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  <ha-icon-button
                    .label=${this.hass.localize("ui.common.help")}
                    .path=${x}
                  >
                  </ha-icon-button
                ></a>
              `:s.s6}
        </ha-dialog-header>
        <div>
          ${this._loading||null===this._step?s.qy`
                <step-flow-loading
                  .flowConfig=${this._params.flowConfig}
                  .hass=${this.hass}
                  .loadingReason=${this._loading}
                  .handler=${this._handler}
                  .step=${this._step}
                ></step-flow-loading>
              `:void 0===this._step?s.s6:s.qy`
                  ${"form"===this._step.type?s.qy`
                        <step-flow-form
                          narrow
                          .flowConfig=${this._params.flowConfig}
                          .step=${this._step}
                          .hass=${this.hass}
                        ></step-flow-form>
                      `:"external"===this._step.type?s.qy`
                          <step-flow-external
                            .flowConfig=${this._params.flowConfig}
                            .step=${this._step}
                            .hass=${this.hass}
                          ></step-flow-external>
                        `:"abort"===this._step.type?s.qy`
                            <step-flow-abort
                              .params=${this._params}
                              .step=${this._step}
                              .hass=${this.hass}
                              .handler=${this._step.handler}
                              .domain=${this._params.domain??this._step.handler}
                            ></step-flow-abort>
                          `:"progress"===this._step.type?s.qy`
                              <step-flow-progress
                                .flowConfig=${this._params.flowConfig}
                                .step=${this._step}
                                .hass=${this.hass}
                                .progress=${this._progress}
                              ></step-flow-progress>
                            `:"menu"===this._step.type?s.qy`
                                <step-flow-menu
                                  .flowConfig=${this._params.flowConfig}
                                  .step=${this._step}
                                  .hass=${this.hass}
                                ></step-flow-menu>
                              `:s.qy`
                                <step-flow-create-entry
                                  .flowConfig=${this._params.flowConfig}
                                  .step=${this._step}
                                  .hass=${this.hass}
                                  .navigateToResult=${this._params.navigateToResult??!1}
                                  .devices=${this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),this._step.result?.entry_id,this._params.carryOverDevices)}
                                ></step-flow-create-entry>
                              `}
                `}
        </div>
      </ha-dialog>
    `}firstUpdated(e){super.firstUpdated(e),this.addEventListener("flow-update",(e=>{const{step:t,stepPromise:o}=e.detail;this._processStep(t||o)}))}willUpdate(e){super.willUpdate(e),e.has("_step")&&this._step&&["external","progress"].includes(this._step.type)&&this._subscribeDataEntryFlowProgressed()}async _processStep(e){if(void 0===e)return void this.closeDialog();const t=setTimeout((()=>{this._loading="loading_step"}),250);let o;try{o=await e}catch(i){return this.closeDialog(),void(0,h.K$)(this,{title:this.hass.localize("ui.panel.config.integrations.config_flow.error"),text:i?.body?.message})}finally{clearTimeout(t),this._loading=void 0}this._step=void 0,await this.updateComplete,this._step=o,"create_entry"!==o.type&&"abort"!==o.type||!o.next_flow||(this._step=void 0,this._handler=void 0,this._unsubDataEntryFlowProgress&&(this._unsubDataEntryFlowProgress(),this._unsubDataEntryFlowProgress=void 0),"config_flow"===o.next_flow[0]?(0,b.W)(this,{continueFlowId:o.next_flow[1],carryOverDevices:this._devices(this._params.flowConfig.showDevices,Object.values(this.hass.devices),"create_entry"===o.type?o.result?.entry_id:void 0,this._params.carryOverDevices).map((e=>e.id)),dialogClosedCallback:this._params.dialogClosedCallback}):"options_flow"===o.next_flow[0]?"create_entry"===o.type&&(0,v.Q)(this,o.result,{continueFlowId:o.next_flow[1],navigateToResult:this._params.navigateToResult,dialogClosedCallback:this._params.dialogClosedCallback}):"config_subentries_flow"===o.next_flow[0]?"create_entry"===o.type&&(0,y.a)(this,o.result,o.next_flow[0],{continueFlowId:o.next_flow[1],navigateToResult:this._params.navigateToResult,dialogClosedCallback:this._params.dialogClosedCallback}):(this.closeDialog(),(0,h.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error",{error:`Unsupported next flow type: ${o.next_flow[0]}`})})))}async _subscribeDataEntryFlowProgressed(){if(this._unsubDataEntryFlowProgress)return;this._progress=void 0;const e=[(0,c.P)(this.hass.connection,(e=>{e.data.flow_id===this._step?.flow_id&&(this._processStep(this._params.flowConfig.fetchFlow(this.hass,this._step.flow_id)),this._progress=void 0)})),(0,c.K)(this.hass.connection,(e=>{this._progress=Math.ceil(100*e.data.progress)}))];this._unsubDataEntryFlowProgress=async()=>{(await Promise.all(e)).map((e=>e()))}}static get styles(){return[d.nA,s.AH`
        ha-dialog {
          --dialog-content-padding: 0;
        }
        .dialog-title {
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .dialog-title.form {
          white-space: normal;
        }
        .help {
          color: var(--secondary-text-color);
        }
      `]}constructor(...e){super(...e),this._instance=z,this._devices=(0,r.A)(((e,t,o,i)=>e&&o?t.filter((e=>e.config_entries.includes(o)||i?.includes(e.id))):[]))}}(0,a.__decorate)([(0,n.MZ)({attribute:!1})],C.prototype,"hass",void 0),(0,a.__decorate)([(0,n.wk)()],C.prototype,"_params",void 0),(0,a.__decorate)([(0,n.wk)()],C.prototype,"_loading",void 0),(0,a.__decorate)([(0,n.wk)()],C.prototype,"_progress",void 0),(0,a.__decorate)([(0,n.wk)()],C.prototype,"_step",void 0),(0,a.__decorate)([(0,n.wk)()],C.prototype,"_handler",void 0),C=(0,a.__decorate)([(0,n.EM)("dialog-data-entry-flow")],C),i()}catch(k){i(k)}}))},73042:function(e,t,o){o.d(t,{W:()=>r});var i=o(96196),a=o(23608),s=o(84125),n=o(73347);const r=(e,t)=>(0,n.g)(e,t,{flowType:"config_flow",showDevices:!0,createFlow:async(e,o)=>{const[i]=await Promise.all([(0,a.t1)(e,o,t.entryId),e.loadFragmentTranslation("config"),e.loadBackendTranslation("config",o),e.loadBackendTranslation("selector",o),e.loadBackendTranslation("title",o)]);return i},fetchFlow:async(e,t)=>{const[o]=await Promise.all([(0,a.PN)(e,t),e.loadFragmentTranslation("config")]);return await Promise.all([e.loadBackendTranslation("config",o.handler),e.loadBackendTranslation("selector",o.handler),e.loadBackendTranslation("title",o.handler)]),o},handleFlowStep:a.jm,deleteFlow:a.sR,renderAbortDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.abort.${t.reason}`,t.description_placeholders);return o?i.qy`
            <ha-markdown allow-svg breaks .content=${o}></ha-markdown>
          `:t.reason},renderShowFormStepHeader(e,t){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.title`,t.description_placeholders)||e.localize(`component.${t.handler}.title`)},renderShowFormStepDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.description`,t.description_placeholders);return o?i.qy`
            <ha-markdown
              .allowDataUrl=${"zwave_js"===t.handler}
              allow-svg
              breaks
              .content=${o}
            ></ha-markdown>
          `:""},renderShowFormStepFieldLabel(e,t,o,i){if("expandable"===o.type)return e.localize(`component.${t.handler}.config.step.${t.step_id}.sections.${o.name}.name`,t.description_placeholders);const a=i?.path?.[0]?`sections.${i.path[0]}.`:"";return e.localize(`component.${t.handler}.config.step.${t.step_id}.${a}data.${o.name}`,t.description_placeholders)||o.name},renderShowFormStepFieldHelper(e,t,o,a){if("expandable"===o.type)return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.sections.${o.name}.description`,t.description_placeholders);const s=a?.path?.[0]?`sections.${a.path[0]}.`:"",n=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.${s}data_description.${o.name}`,t.description_placeholders);return n?i.qy`<ha-markdown breaks .content=${n}></ha-markdown>`:""},renderShowFormStepFieldError(e,t,o){return e.localize(`component.${t.translation_domain||t.translation_domain||t.handler}.config.error.${o}`,t.description_placeholders)||o},renderShowFormStepFieldLocalizeValue(e,t,o){return e.localize(`component.${t.handler}.selector.${o}`)},renderShowFormStepSubmitButton(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.submit`)||e.localize("ui.panel.config.integrations.config_flow."+(!1===t.last_step?"next":"submit"))},renderExternalStepHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize("ui.panel.config.integrations.config_flow.external_step.open_site")},renderExternalStepDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.${t.step_id}.description`,t.description_placeholders);return i.qy`
        <p>
          ${e.localize("ui.panel.config.integrations.config_flow.external_step.description")}
        </p>
        ${o?i.qy`
              <ha-markdown
                allow-svg
                breaks
                .content=${o}
              ></ha-markdown>
            `:""}
      `},renderCreateEntryDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.create_entry.${t.description||"default"}`,t.description_placeholders);return i.qy`
        ${o?i.qy`
              <ha-markdown
                allow-svg
                breaks
                .content=${o}
              ></ha-markdown>
            `:i.s6}
      `},renderShowFormProgressHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize(`component.${t.handler}.title`)},renderShowFormProgressDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.progress.${t.progress_action}`,t.description_placeholders);return o?i.qy`
            <ha-markdown allow-svg breaks .content=${o}></ha-markdown>
          `:""},renderMenuHeader(e,t){return e.localize(`component.${t.handler}.config.step.${t.step_id}.title`)||e.localize(`component.${t.handler}.title`)},renderMenuDescription(e,t){const o=e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.description`,t.description_placeholders);return o?i.qy`
            <ha-markdown allow-svg breaks .content=${o}></ha-markdown>
          `:""},renderMenuOption(e,t,o){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.menu_options.${o}`,t.description_placeholders)},renderMenuOptionDescription(e,t,o){return e.localize(`component.${t.translation_domain||t.handler}.config.step.${t.step_id}.menu_option_descriptions.${o}`,t.description_placeholders)},renderLoadingDescription(e,t,o,i){if("loading_flow"!==t&&"loading_step"!==t)return"";const a=i?.handler||o;return e.localize(`ui.panel.config.integrations.config_flow.loading.${t}`,{integration:a?(0,s.p$)(e.localize,a):e.localize("ui.panel.config.integrations.config_flow.loading.fallback_title")})}})},35804:function(e,t,o){o.d(t,{Q:()=>d});var i=o(96196),a=o(84125);const s=(e,t)=>e.callApi("POST","config/config_entries/options/flow",{handler:t,show_advanced_options:Boolean(e.userData?.showAdvanced)}),n=(e,t)=>e.callApi("GET",`config/config_entries/options/flow/${t}`),r=(e,t,o)=>e.callApi("POST",`config/config_entries/options/flow/${t}`,o),l=(e,t)=>e.callApi("DELETE",`config/config_entries/options/flow/${t}`);var c=o(73347);const d=(e,t,o)=>(0,c.g)(e,{startFlowHandler:t.entry_id,domain:t.domain,...o},{flowType:"options_flow",showDevices:!1,createFlow:async(e,o)=>{const[i]=await Promise.all([s(e,o),e.loadFragmentTranslation("config"),e.loadBackendTranslation("options",t.domain),e.loadBackendTranslation("selector",t.domain)]);return i},fetchFlow:async(e,o)=>{const[i]=await Promise.all([n(e,o),e.loadFragmentTranslation("config"),e.loadBackendTranslation("options",t.domain),e.loadBackendTranslation("selector",t.domain)]);return i},handleFlowStep:r,deleteFlow:l,renderAbortDescription(e,o){const a=e.localize(`component.${o.translation_domain||t.domain}.options.abort.${o.reason}`,o.description_placeholders);return a?i.qy`
              <ha-markdown
                breaks
                allow-svg
                .content=${a}
              ></ha-markdown>
            `:o.reason},renderShowFormStepHeader(e,o){return e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.title`,o.description_placeholders)||e.localize("ui.dialogs.options_flow.form.header")},renderShowFormStepDescription(e,o){const a=e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.description`,o.description_placeholders);return a?i.qy`
              <ha-markdown
                allow-svg
                breaks
                .content=${a}
              ></ha-markdown>
            `:""},renderShowFormStepFieldLabel(e,o,i,a){if("expandable"===i.type)return e.localize(`component.${t.domain}.options.step.${o.step_id}.sections.${i.name}.name`,o.description_placeholders);const s=a?.path?.[0]?`sections.${a.path[0]}.`:"";return e.localize(`component.${t.domain}.options.step.${o.step_id}.${s}data.${i.name}`,o.description_placeholders)||i.name},renderShowFormStepFieldHelper(e,o,a,s){if("expandable"===a.type)return e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.sections.${a.name}.description`,o.description_placeholders);const n=s?.path?.[0]?`sections.${s.path[0]}.`:"",r=e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.${n}data_description.${a.name}`,o.description_placeholders);return r?i.qy`<ha-markdown breaks .content=${r}></ha-markdown>`:""},renderShowFormStepFieldError(e,o,i){return e.localize(`component.${o.translation_domain||t.domain}.options.error.${i}`,o.description_placeholders)||i},renderShowFormStepFieldLocalizeValue(e,o,i){return e.localize(`component.${t.domain}.selector.${i}`)},renderShowFormStepSubmitButton(e,o){return e.localize(`component.${t.domain}.options.step.${o.step_id}.submit`)||e.localize("ui.panel.config.integrations.config_flow."+(!1===o.last_step?"next":"submit"))},renderExternalStepHeader(e,t){return""},renderExternalStepDescription(e,t){return""},renderCreateEntryDescription(e,t){return i.qy`
          <p>${e.localize("ui.dialogs.options_flow.success.description")}</p>
        `},renderShowFormProgressHeader(e,o){return e.localize(`component.${t.domain}.options.step.${o.step_id}.title`)||e.localize(`component.${t.domain}.title`)},renderShowFormProgressDescription(e,o){const a=e.localize(`component.${o.translation_domain||t.domain}.options.progress.${o.progress_action}`,o.description_placeholders);return a?i.qy`
              <ha-markdown
                allow-svg
                breaks
                .content=${a}
              ></ha-markdown>
            `:""},renderMenuHeader(e,o){return e.localize(`component.${t.domain}.options.step.${o.step_id}.title`)||e.localize(`component.${t.domain}.title`)},renderMenuDescription(e,o){const a=e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.description`,o.description_placeholders);return a?i.qy`
              <ha-markdown
                allow-svg
                breaks
                .content=${a}
              ></ha-markdown>
            `:""},renderMenuOption(e,o,i){return e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.menu_options.${i}`,o.description_placeholders)},renderMenuOptionDescription(e,o,i){return e.localize(`component.${o.translation_domain||t.domain}.options.step.${o.step_id}.menu_option_descriptions.${i}`,o.description_placeholders)},renderLoadingDescription(e,o){return e.localize(`component.${t.domain}.options.loading`)||("loading_flow"===o||"loading_step"===o?e.localize(`ui.dialogs.options_flow.loading.${o}`,{integration:(0,a.p$)(e.localize,t.domain)}):"")}})},53264:function(e,t,o){o.d(t,{a:()=>d});var i=o(96196),a=o(84125);const s={"HA-Frontend-Base":`${location.protocol}//${location.host}`},n=(e,t,o,i)=>e.callApi("POST","config/config_entries/subentries/flow",{handler:[t,o],show_advanced_options:Boolean(e.userData?.showAdvanced),subentry_id:i},s),r=(e,t,o)=>e.callApi("POST",`config/config_entries/subentries/flow/${t}`,o,s),l=(e,t)=>e.callApi("DELETE",`config/config_entries/subentries/flow/${t}`);var c=o(73347);const d=(e,t,o,d)=>(0,c.g)(e,d,{flowType:"config_subentries_flow",showDevices:!0,createFlow:async(e,i)=>{const[a]=await Promise.all([n(e,i,o,d.subEntryId),e.loadFragmentTranslation("config"),e.loadBackendTranslation("config_subentries",t.domain),e.loadBackendTranslation("selector",t.domain),e.loadBackendTranslation("title",t.domain)]);return a},fetchFlow:async(e,o)=>{const i=await((e,t)=>e.callApi("GET",`config/config_entries/subentries/flow/${t}`,void 0,s))(e,o);return await e.loadFragmentTranslation("config"),await e.loadBackendTranslation("config_subentries",t.domain),await e.loadBackendTranslation("selector",t.domain),i},handleFlowStep:r,deleteFlow:l,renderAbortDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.abort.${a.reason}`,a.description_placeholders);return s?i.qy`
            <ha-markdown allowsvg breaks .content=${s}></ha-markdown>
          `:a.reason},renderShowFormStepHeader(e,i){return e.localize(`component.${i.translation_domain||t.domain}.config_subentries.${o}.step.${i.step_id}.title`,i.description_placeholders)||e.localize(`component.${t.domain}.title`)},renderShowFormStepDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.step.${a.step_id}.description`,a.description_placeholders);return s?i.qy`
            <ha-markdown allowsvg breaks .content=${s}></ha-markdown>
          `:""},renderShowFormStepFieldLabel(e,i,a,s){if("expandable"===a.type)return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.sections.${a.name}.name`,i.description_placeholders);const n=s?.path?.[0]?`sections.${s.path[0]}.`:"";return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.${n}data.${a.name}`,i.description_placeholders)||a.name},renderShowFormStepFieldHelper(e,a,s,n){if("expandable"===s.type)return e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.step.${a.step_id}.sections.${s.name}.description`,a.description_placeholders);const r=n?.path?.[0]?`sections.${n.path[0]}.`:"",l=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.step.${a.step_id}.${r}data_description.${s.name}`,a.description_placeholders);return l?i.qy`<ha-markdown breaks .content=${l}></ha-markdown>`:""},renderShowFormStepFieldError(e,i,a){return e.localize(`component.${i.translation_domain||i.translation_domain||t.domain}.config_subentries.${o}.error.${a}`,i.description_placeholders)||a},renderShowFormStepFieldLocalizeValue(e,o,i){return e.localize(`component.${t.domain}.selector.${i}`)},renderShowFormStepSubmitButton(e,i){return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.submit`)||e.localize("ui.panel.config.integrations.config_flow."+(!1===i.last_step?"next":"submit"))},renderExternalStepHeader(e,i){return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.title`)||e.localize("ui.panel.config.integrations.config_flow.external_step.open_site")},renderExternalStepDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.step.${a.step_id}.description`,a.description_placeholders);return i.qy`
        <p>
          ${e.localize("ui.panel.config.integrations.config_flow.external_step.description")}
        </p>
        ${s?i.qy`
              <ha-markdown
                allowsvg
                breaks
                .content=${s}
              ></ha-markdown>
            `:""}
      `},renderCreateEntryDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.create_entry.${a.description||"default"}`,a.description_placeholders);return i.qy`
        ${s?i.qy`
              <ha-markdown
                allowsvg
                breaks
                .content=${s}
              ></ha-markdown>
            `:i.s6}
      `},renderShowFormProgressHeader(e,i){return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.title`)||e.localize(`component.${t.domain}.title`)},renderShowFormProgressDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.progress.${a.progress_action}`,a.description_placeholders);return s?i.qy`
            <ha-markdown allowsvg breaks .content=${s}></ha-markdown>
          `:""},renderMenuHeader(e,i){return e.localize(`component.${t.domain}.config_subentries.${o}.step.${i.step_id}.title`,i.description_placeholders)||e.localize(`component.${t.domain}.title`)},renderMenuDescription(e,a){const s=e.localize(`component.${a.translation_domain||t.domain}.config_subentries.${o}.step.${a.step_id}.description`,a.description_placeholders);return s?i.qy`
            <ha-markdown allowsvg breaks .content=${s}></ha-markdown>
          `:""},renderMenuOption(e,i,a){return e.localize(`component.${i.translation_domain||t.domain}.config_subentries.${o}.step.${i.step_id}.menu_options.${a}`,i.description_placeholders)},renderMenuOptionDescription(e,i,a){return e.localize(`component.${i.translation_domain||t.domain}.config_subentries.${o}.step.${i.step_id}.menu_option_descriptions.${a}`,i.description_placeholders)},renderLoadingDescription(e,t,o,i){if("loading_flow"!==t&&"loading_step"!==t)return"";const s=i?.handler||o;return e.localize(`ui.panel.config.integrations.config_flow.loading.${t}`,{integration:s?(0,a.p$)(e.localize,s):e.localize("ui.panel.config.integrations.config_flow.loading.fallback_title")})}})},93056:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(92542),r=o(78778),l=o(73042),c=o(97854),d=o(89473),p=e([d]);d=(p.then?(await p)():p)[0];class h extends a.WF{firstUpdated(e){super.firstUpdated(e),"missing_credentials"===this.step.reason&&this._handleMissingCreds()}render(){return"missing_credentials"===this.step.reason?a.s6:a.qy`
      <div class="content">
        ${this.params.flowConfig.renderAbortDescription(this.hass,this.step)}
      </div>
      <div class="buttons">
        <ha-button appearance="plain" @click=${this._flowDone}
          >${this.hass.localize("ui.panel.config.integrations.config_flow.close")}</ha-button
        >
      </div>
    `}async _handleMissingCreds(){(0,r.a)(this.params.dialogParentElement,{selectedDomain:this.domain,manifest:this.params.manifest,applicationCredentialAddedCallback:()=>{(0,l.W)(this.params.dialogParentElement,{dialogClosedCallback:this.params.dialogClosedCallback,startFlowHandler:this.handler,showAdvanced:this.hass.userData?.showAdvanced,navigateToResult:this.params.navigateToResult})}}),this._flowDone()}_flowDone(){(0,n.r)(this,"flow-update",{step:void 0})}static get styles(){return c.G}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"params",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"step",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"domain",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],h.prototype,"handler",void 0),h=(0,i.__decorate)([(0,s.EM)("step-flow-abort")],h),t()}catch(h){t(h)}}))},64533:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(22786),r=o(92542),l=o(16727),c=o(41144),d=o(5871),p=o(53907),h=o(89473),m=o(41558),_=o(1491),u=o(22800),g=o(84125),f=o(76681),w=o(10234),v=o(6358),y=o(97854),b=o(3950),$=e([p,h]);[p,h]=$.then?(await $)():$;class k extends a.WF{firstUpdated(e){super.firstUpdated(e),this._loadDomains()}willUpdate(e){if(!e.has("devices")&&!e.has("hass"))return;if(1!==this.devices.length||this.devices[0].primary_config_entry!==this.step.result?.entry_id||"voip"===this.step.result.domain)return;const t=this._deviceEntities(this.devices[0].id,Object.values(this.hass.entities),"assist_satellite");t.length&&t.some((e=>(0,m.KC)(this.hass.states[e.entity_id])))&&(this.navigateToResult=!1,this._flowDone(),(0,v.L)(this,{deviceId:this.devices[0].id}))}render(){const e=this.hass.localize,t=this.step.result?{...this._domains,[this.step.result.entry_id]:this.step.result.domain}:this._domains;return a.qy`
      <div class="content">
        ${this.flowConfig.renderCreateEntryDescription(this.hass,this.step)}
        ${"not_loaded"===this.step.result?.state?a.qy`<span class="error"
              >${e("ui.panel.config.integrations.config_flow.not_loaded")}</span
            >`:a.s6}
        ${0===this.devices.length&&["options_flow","repair_flow"].includes(this.flowConfig.flowType)?a.s6:0===this.devices.length?a.qy`<p>
                ${e("ui.panel.config.integrations.config_flow.created_config",{name:this.step.title})}
              </p>`:a.qy`
                <div class="devices">
                  ${this.devices.map((o=>a.qy`
                      <div class="device">
                        <div class="device-info">
                          ${o.primary_config_entry&&t[o.primary_config_entry]?a.qy`<img
                                slot="graphic"
                                alt=${(0,g.p$)(this.hass.localize,t[o.primary_config_entry])}
                                src=${(0,f.MR)({domain:t[o.primary_config_entry],type:"icon",darkOptimized:this.hass.themes?.darkMode})}
                                crossorigin="anonymous"
                                referrerpolicy="no-referrer"
                              />`:a.s6}
                          <div class="device-info-details">
                            <span>${o.model||o.manufacturer}</span>
                            ${o.model?a.qy`<span class="secondary">
                                  ${o.manufacturer}
                                </span>`:a.s6}
                          </div>
                        </div>
                        <ha-textfield
                          .label=${e("ui.panel.config.integrations.config_flow.device_name")}
                          .placeholder=${(0,l.T)(o,this.hass)}
                          .value=${this._deviceUpdate[o.id]?.name??(0,l.xn)(o)}
                          @change=${this._deviceNameChanged}
                          .device=${o.id}
                        ></ha-textfield>
                        <ha-area-picker
                          .hass=${this.hass}
                          .device=${o.id}
                          .value=${this._deviceUpdate[o.id]?.area??o.area_id??void 0}
                          @value-changed=${this._areaPicked}
                        ></ha-area-picker>
                      </div>
                    `))}
                </div>
              `}
      </div>
      <div class="buttons">
        <ha-button @click=${this._flowDone}
          >${e("ui.panel.config.integrations.config_flow."+(!this.devices.length||Object.keys(this._deviceUpdate).length?"finish":"finish_skip"))}</ha-button
        >
      </div>
    `}async _loadDomains(){const e=await(0,b.VN)(this.hass);this._domains=Object.fromEntries(e.map((e=>[e.entry_id,e.domain])))}async _flowDone(){if(Object.keys(this._deviceUpdate).length){const e=[],t=Object.entries(this._deviceUpdate).map((([t,o])=>(o.name&&e.push(t),(0,_.FB)(this.hass,t,{name_by_user:o.name,area_id:o.area}).catch((e=>{(0,w.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error_saving_device",{error:e.message})})})))));await Promise.allSettled(t);const o=[],i=[];e.forEach((e=>{const t=this._deviceEntities(e,Object.values(this.hass.entities));i.push(...t.map((e=>e.entity_id)))}));const a=await(0,u.BM)(this.hass,i);Object.entries(a).forEach((([e,t])=>{t&&o.push((0,u.G_)(this.hass,e,{new_entity_id:t}).catch((e=>(0,w.K$)(this,{text:this.hass.localize("ui.panel.config.integrations.config_flow.error_saving_entity",{error:e.message})}))))})),await Promise.allSettled(o)}(0,r.r)(this,"flow-update",{step:void 0}),this.step.result&&this.navigateToResult&&(1===this.devices.length?(0,d.o)(`/config/devices/device/${this.devices[0].id}`):(0,d.o)(`/config/integrations/integration/${this.step.result.domain}#config_entry=${this.step.result.entry_id}`))}async _areaPicked(e){const t=e.currentTarget.device,o=e.detail.value;t in this._deviceUpdate||(this._deviceUpdate[t]={}),this._deviceUpdate[t].area=o,this.requestUpdate("_deviceUpdate")}_deviceNameChanged(e){const t=e.currentTarget,o=t.device,i=t.value;o in this._deviceUpdate||(this._deviceUpdate[o]={}),this._deviceUpdate[o].name=i,this.requestUpdate("_deviceUpdate")}static get styles(){return[y.G,a.AH`
        .devices {
          display: flex;
          margin: -4px;
          max-height: 600px;
          overflow-y: auto;
          flex-direction: column;
        }
        @media all and (max-width: 450px), all and (max-height: 500px) {
          .devices {
            /* header - margin content - footer */
            max-height: calc(100vh - 52px - 20px - 52px);
          }
        }
        .device {
          border: 1px solid var(--divider-color);
          padding: 6px;
          border-radius: var(--ha-border-radius-sm);
          margin: 4px;
          display: inline-block;
        }
        .device-info {
          display: flex;
          align-items: center;
          gap: var(--ha-space-2);
        }
        .device-info img {
          width: 40px;
          height: 40px;
        }
        .device-info-details {
          display: flex;
          flex-direction: column;
          justify-content: center;
        }
        .secondary {
          color: var(--secondary-text-color);
        }
        ha-textfield,
        ha-area-picker {
          display: block;
        }
        ha-textfield {
          margin: 8px 0;
        }
        .buttons > *:last-child {
          margin-left: auto;
          margin-inline-start: auto;
          margin-inline-end: initial;
        }
        .error {
          color: var(--error-color);
        }
      `]}constructor(...e){super(...e),this._domains={},this.navigateToResult=!1,this._deviceUpdate={},this._deviceEntities=(0,n.A)(((e,t,o)=>t.filter((t=>t.device_id===e&&(!o||(0,c.m)(t.entity_id)===o)))))}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],k.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],k.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],k.prototype,"step",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],k.prototype,"devices",void 0),(0,i.__decorate)([(0,s.wk)()],k.prototype,"_deviceUpdate",void 0),k=(0,i.__decorate)([(0,s.EM)("step-flow-create-entry")],k),t()}catch(k){t(k)}}))},12083:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(97854),r=o(89473),l=e([r]);r=(l.then?(await l)():l)[0];class c extends a.WF{render(){const e=this.hass.localize;return a.qy`
      <div class="content">
        ${this.flowConfig.renderExternalStepDescription(this.hass,this.step)}
        <div class="open-button">
          <ha-button href=${this.step.url} target="_blank" rel="noreferrer">
            ${e("ui.panel.config.integrations.config_flow.external_step.open_site")}
          </ha-button>
        </div>
      </div>
    `}firstUpdated(e){super.firstUpdated(e),window.open(this.step.url)}static get styles(){return[n.G,a.AH`
        .open-button {
          text-align: center;
          padding: 24px 0;
        }
        .open-button a {
          text-decoration: none;
        }
      `]}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"step",void 0),c=(0,i.__decorate)([(0,s.EM)("step-flow-external")],c),t()}catch(c){t(c)}}))},84398:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(22786),r=o(51757),l=o(92542),c=o(45817),d=o(89473),p=(o(17963),o(23442)),h=(o(91120),o(28089),o(89600)),m=o(54193),_=o(73103),u=o(39396),g=o(97854),f=e([d,h]);[d,h]=f.then?(await f)():f;class w extends a.WF{disconnectedCallback(){super.disconnectedCallback(),this.removeEventListener("keydown",this._handleKeyDown)}render(){const e=this.step,t=this._stepDataProcessed;return a.qy`
      <div class="content" @click=${this._clickHandler}>
        ${this.flowConfig.renderShowFormStepDescription(this.hass,this.step)}
        ${this._errorMsg?a.qy`<ha-alert alert-type="error">${this._errorMsg}</ha-alert>`:""}
        <ha-form
          .hass=${this.hass}
          .narrow=${this.narrow}
          .data=${t}
          .disabled=${this._loading}
          @value-changed=${this._stepDataChanged}
          .schema=${(0,m.Hg)(this.handleReadOnlyFields(e.data_schema))}
          .error=${this._errors}
          .computeLabel=${this._labelCallback}
          .computeHelper=${this._helperCallback}
          .computeError=${this._errorCallback}
          .localizeValue=${this._localizeValueCallback}
        ></ha-form>
      </div>
      ${e.preview?a.qy`<div class="preview" @set-flow-errors=${this._setError}>
            <h3>
              ${this.hass.localize("ui.panel.config.integrations.config_flow.preview")}:
            </h3>
            ${(0,r._)(`flow-preview-${(0,_.F)(e.preview)}`,{hass:this.hass,domain:e.preview,flowType:this.flowConfig.flowType,handler:e.handler,stepId:e.step_id,flowId:e.flow_id,stepData:t})}
          </div>`:a.s6}
      <div class="buttons">
        <ha-button @click=${this._submitStep} .loading=${this._loading}>
          ${this.flowConfig.renderShowFormStepSubmitButton(this.hass,this.step)}
        </ha-button>
      </div>
    `}_setError(e){this._previewErrors=e.detail}firstUpdated(e){super.firstUpdated(e),setTimeout((()=>this.shadowRoot.querySelector("ha-form").focus()),0),this.addEventListener("keydown",this._handleKeyDown)}willUpdate(e){super.willUpdate(e),e.has("step")&&this.step?.preview&&o(25115)(`./flow-preview-${(0,_.F)(this.step.preview)}`),(e.has("step")||e.has("_previewErrors")||e.has("_submitErrors"))&&(this._errors=this.step.errors||this._previewErrors||this._submitErrors?{...this.step.errors,...this._previewErrors,...this._submitErrors}:void 0)}_clickHandler(e){(0,c.d)(e,!1)&&(0,l.r)(this,"flow-update",{step:void 0})}get _stepDataProcessed(){return void 0!==this._stepData||(this._stepData=(0,p.$)(this.step.data_schema)),this._stepData}async _submitStep(){const e=this._stepData||{},t=(e,o)=>e.every((e=>(!e.required||!["",void 0].includes(o[e.name]))&&("expandable"!==e.type||!e.required&&void 0===o[e.name]||t(e.schema,o[e.name]))));if(!(void 0===e?void 0===this.step.data_schema.find((e=>e.required)):t(this.step.data_schema,e)))return void(this._errorMsg=this.hass.localize("ui.panel.config.integrations.config_flow.not_all_required_fields"));this._loading=!0,this._errorMsg=void 0,this._submitErrors=void 0;const o=this.step.flow_id,i={};Object.keys(e).forEach((t=>{const o=e[t],a=[void 0,""].includes(o),s=this.step.data_schema?.find((e=>e.name===t)),n=s?.selector??{},r=Object.values(n)[0]?.read_only;a||r||(i[t]=o)}));try{const e=await this.flowConfig.handleFlowStep(this.hass,this.step.flow_id,i);if(!this.step||o!==this.step.flow_id)return;this._previewErrors=void 0,(0,l.r)(this,"flow-update",{step:e})}catch(a){a&&a.body?(a.body.message&&(this._errorMsg=a.body.message),a.body.errors&&(this._submitErrors=a.body.errors),a.body.message||a.body.errors||(this._errorMsg="Unknown error occurred")):this._errorMsg="Unknown error occurred"}finally{this._loading=!1}}_stepDataChanged(e){this._stepData=e.detail.value}static get styles(){return[u.RF,g.G,a.AH`
        .error {
          color: red;
        }

        ha-alert,
        ha-form {
          margin-top: 24px;
          display: block;
        }

        .buttons {
          padding: 16px;
        }
      `]}constructor(...e){super(...e),this.narrow=!1,this._loading=!1,this.handleReadOnlyFields=(0,n.A)((e=>e?.map((e=>({...e,...Object.values(e?.selector??{})[0]?.read_only?{disabled:!0}:{}}))))),this._handleKeyDown=e=>{"Enter"===e.key&&this._submitStep()},this._labelCallback=(e,t,o)=>this.flowConfig.renderShowFormStepFieldLabel(this.hass,this.step,e,o),this._helperCallback=(e,t)=>this.flowConfig.renderShowFormStepFieldHelper(this.hass,this.step,e,t),this._errorCallback=e=>this.flowConfig.renderShowFormStepFieldError(this.hass,this.step,e),this._localizeValueCallback=e=>this.flowConfig.renderShowFormStepFieldLocalizeValue(this.hass,this.step,e)}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],w.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({type:Boolean})],w.prototype,"narrow",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],w.prototype,"step",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,i.__decorate)([(0,s.wk)()],w.prototype,"_loading",void 0),(0,i.__decorate)([(0,s.wk)()],w.prototype,"_stepData",void 0),(0,i.__decorate)([(0,s.wk)()],w.prototype,"_previewErrors",void 0),(0,i.__decorate)([(0,s.wk)()],w.prototype,"_submitErrors",void 0),(0,i.__decorate)([(0,s.wk)()],w.prototype,"_errorMsg",void 0),w=(0,i.__decorate)([(0,s.EM)("step-flow-form")],w),t()}catch(w){t(w)}}))},19486:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(89600),r=e([n]);n=(r.then?(await r)():r)[0];class l extends a.WF{render(){const e=this.flowConfig.renderLoadingDescription(this.hass,this.loadingReason,this.handler,this.step);return a.qy`
      <div class="content">
        <ha-spinner size="large"></ha-spinner>
        ${e?a.qy`<div>${e}</div>`:""}
      </div>
    `}}l.styles=a.AH`
    .content {
      margin-top: 0;
      padding: 50px 100px;
      text-align: center;
    }
    ha-spinner {
      margin-bottom: 16px;
    }
  `,(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"loadingReason",void 0),(0,i.__decorate)([(0,s.MZ)()],l.prototype,"handler",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],l.prototype,"step",void 0),l=(0,i.__decorate)([(0,s.EM)("step-flow-loading")],l),t()}catch(l){t(l)}}))},59395:function(e,t,o){var i=o(62826),a=o(96196),s=o(77845),n=o(92542),r=(o(28608),o(56565),o(97854)),l=o(25749);class c extends a.WF{shouldUpdate(e){return e.size>1||!e.has("hass")||this.hass.localize!==e.get("hass")?.localize}render(){let e,t,o={};if(Array.isArray(this.step.menu_options)){e=this.step.menu_options,t={};for(const i of e)t[i]=this.flowConfig.renderMenuOption(this.hass,this.step,i),o[i]=this.flowConfig.renderMenuOptionDescription(this.hass,this.step,i)}else e=Object.keys(this.step.menu_options),t=this.step.menu_options,o=Object.fromEntries(e.map((e=>[e,this.flowConfig.renderMenuOptionDescription(this.hass,this.step,e)])));this.step.sort&&(e=e.sort(((e,o)=>(0,l.xL)(t[e],t[o],this.hass.locale.language))));const i=this.flowConfig.renderMenuDescription(this.hass,this.step);return a.qy`
      ${i?a.qy`<div class="content">${i}</div>`:""}
      <div class="options">
        ${e.map((e=>a.qy`
            <ha-list-item
              hasMeta
              .step=${e}
              @click=${this._handleStep}
              ?twoline=${o[e]}
              ?multiline-secondary=${o[e]}
            >
              <span>${t[e]}</span>
              ${o[e]?a.qy`<span slot="secondary">
                    ${o[e]}
                  </span>`:a.s6}
              <ha-icon-next slot="meta"></ha-icon-next>
            </ha-list-item>
          `))}
      </div>
    `}_handleStep(e){(0,n.r)(this,"flow-update",{stepPromise:this.flowConfig.handleFlowStep(this.hass,this.step.flow_id,{next_step_id:e.currentTarget.step})})}}c.styles=[r.G,a.AH`
      .options {
        margin-top: 20px;
        margin-bottom: 16px;
      }
      .content {
        padding-bottom: 16px;
      }
      .content + .options {
        margin-top: 8px;
      }
      ha-list-item {
        --mdc-list-side-padding: 24px;
      }
    `],(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],c.prototype,"step",void 0),c=(0,i.__decorate)([(0,s.EM)("step-flow-menu")],c)},12527:function(e,t,o){o.a(e,(async function(e,t){try{var i=o(62826),a=o(96196),s=o(77845),n=o(48565),r=o(64109),l=o(89600),c=o(97854),d=e([r,l]);[r,l]=d.then?(await d)():d;class p extends a.WF{render(){return a.qy`
      <div class="content">
        ${this.progress?a.qy`
              <ha-progress-ring .value=${this.progress} size="large"
                >${this.progress}${(0,n.d)(this.hass.locale)}%</ha-progress-ring
              >
            `:a.qy`<ha-spinner size="large"></ha-spinner>`}
        ${this.flowConfig.renderShowFormProgressDescription(this.hass,this.step)}
      </div>
    `}static get styles(){return[c.G,a.AH`
        .content {
          margin-top: 0;
          padding: 50px 100px;
          text-align: center;
        }
        ha-spinner {
          margin-bottom: 16px;
        }
      `]}}(0,i.__decorate)([(0,s.MZ)({attribute:!1})],p.prototype,"flowConfig",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,i.__decorate)([(0,s.MZ)({attribute:!1})],p.prototype,"step",void 0),(0,i.__decorate)([(0,s.MZ)({type:Number})],p.prototype,"progress",void 0),p=(0,i.__decorate)([(0,s.EM)("step-flow-progress")],p),t()}catch(p){t(p)}}))},97854:function(e,t,o){o.d(t,{G:()=>i});const i=o(96196).AH`
  h2 {
    margin: 24px 38px 0 0;
    margin-inline-start: 0px;
    margin-inline-end: 38px;
    padding: 0 24px;
    padding-inline-start: 24px;
    padding-inline-end: 24px;
    -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
    -webkit-font-smoothing: var(--ha-font-smoothing);
    font-family: var(
      --mdc-typography-headline6-font-family,
      var(--mdc-typography-font-family, var(--ha-font-family-body))
    );
    font-size: var(--mdc-typography-headline6-font-size, var(--ha-font-size-l));
    line-height: var(--mdc-typography-headline6-line-height, 2rem);
    font-weight: var(
      --mdc-typography-headline6-font-weight,
      var(--ha-font-weight-medium)
    );
    letter-spacing: var(--mdc-typography-headline6-letter-spacing, 0.0125em);
    text-decoration: var(--mdc-typography-headline6-text-decoration, inherit);
    text-transform: var(--mdc-typography-headline6-text-transform, inherit);
    box-sizing: border-box;
  }

  .content,
  .preview {
    margin-top: 20px;
    padding: 0 24px;
  }

  .buttons {
    position: relative;
    padding: 16px;
    margin: 8px 0 0;
    color: var(--primary-color);
    display: flex;
    justify-content: flex-end;
  }

  ha-markdown {
    overflow-wrap: break-word;
  }
  ha-markdown a {
    color: var(--primary-color);
  }
  ha-markdown img:first-child:last-child {
    display: block;
    margin: 0 auto;
  }
`},6358:function(e,t,o){o.d(t,{L:()=>s});var i=o(92542);const a=()=>Promise.all([o.e("2016"),o.e("3806"),o.e("5633"),o.e("1746")]).then(o.bind(o,54728)),s=(e,t)=>{(0,i.r)(e,"show-dialog",{dialogTag:"ha-voice-assistant-setup-dialog",dialogImport:a,dialogParams:t})}},78778:function(e,t,o){o.d(t,{a:()=>s});var i=o(92542);const a=()=>Promise.all([o.e("9747"),o.e("8451")]).then(o.bind(o,71614)),s=(e,t)=>{(0,i.r)(e,"show-dialog",{dialogTag:"dialog-add-application-credential",dialogImport:a,dialogParams:t})}},76681:function(e,t,o){o.d(t,{MR:()=>i,a_:()=>a,bg:()=>s});const i=e=>`https://brands.home-assistant.io/${e.brand?"brands/":""}${e.useFallback?"_/":""}${e.domain}/${e.darkOptimized?"dark_":""}${e.type}.png`,a=e=>e.split("/")[4],s=e=>e.startsWith("https://brands.home-assistant.io/")},62001:function(e,t,o){o.d(t,{o:()=>i});const i=(e,t)=>`https://${e.config.version.includes("b")?"rc":e.config.version.includes("dev")?"next":"www"}.home-assistant.io${t}`},2355:function(e,t,o){o.d(t,{A:()=>i});const i=o(96196).AH`:host {
  --size: 8rem;
  --track-width: 0.25em;
  --track-color: var(--wa-color-neutral-fill-normal);
  --indicator-width: var(--track-width);
  --indicator-color: var(--wa-color-brand-fill-loud);
  --indicator-transition-duration: 0.35s;
  display: inline-flex;
}
.progress-ring {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.image {
  width: var(--size);
  height: var(--size);
  rotate: -90deg;
  transform-origin: 50% 50%;
}
.track,
.indicator {
  --radius: calc(var(--size) / 2 - max(var(--track-width), var(--indicator-width)) * 0.5);
  --circumference: calc(var(--radius) * 2 * 3.141592654);
  fill: none;
  r: var(--radius);
  cx: calc(var(--size) / 2);
  cy: calc(var(--size) / 2);
}
.track {
  stroke: var(--track-color);
  stroke-width: var(--track-width);
}
.indicator {
  stroke: var(--indicator-color);
  stroke-width: var(--indicator-width);
  stroke-linecap: round;
  transition-property: stroke-dashoffset;
  transition-duration: var(--indicator-transition-duration);
  stroke-dasharray: var(--circumference) var(--circumference);
  stroke-dashoffset: calc(var(--circumference) - var(--percentage) * var(--circumference));
}
.label {
  display: flex;
  align-items: center;
  justify-content: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  text-align: center;
  user-select: none;
  -webkit-user-select: none;
}
`},65686:function(e,t,o){o.a(e,(async function(e,i){try{o.d(t,{A:()=>m});var a=o(96196),s=o(77845),n=o(32510),r=o(17060),l=o(2355),c=e([r]);r=(c.then?(await c)():c)[0];var d=Object.defineProperty,p=Object.getOwnPropertyDescriptor,h=(e,t,o,i)=>{for(var a,s=i>1?void 0:i?p(t,o):t,n=e.length-1;n>=0;n--)(a=e[n])&&(s=(i?a(t,o,s):a(s))||s);return i&&s&&d(t,o,s),s};let m=class extends n.A{updated(e){if(super.updated(e),e.has("value")){const e=parseFloat(getComputedStyle(this.indicator).getPropertyValue("r")),t=2*Math.PI*e,o=t-this.value/100*t;this.indicatorOffset=`${o}px`}}render(){return a.qy`
      <div
        part="base"
        class="progress-ring"
        role="progressbar"
        aria-label=${this.label.length>0?this.label:this.localize.term("progress")}
        aria-describedby="label"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow="${this.value}"
        style="--percentage: ${this.value/100}"
      >
        <svg class="image">
          <circle class="track"></circle>
          <circle class="indicator" style="stroke-dashoffset: ${this.indicatorOffset}"></circle>
        </svg>

        <slot id="label" part="label" class="label"></slot>
      </div>
    `}constructor(){super(...arguments),this.localize=new r.c(this),this.value=0,this.label=""}};m.css=l.A,h([(0,s.P)(".indicator")],m.prototype,"indicator",2),h([(0,s.wk)()],m.prototype,"indicatorOffset",2),h([(0,s.MZ)({type:Number,reflect:!0})],m.prototype,"value",2),h([(0,s.MZ)()],m.prototype,"label",2),m=h([(0,s.EM)("wa-progress-ring")],m),i()}catch(m){i(m)}}))}};
//# sourceMappingURL=7394.6661049e9699e227.js.map