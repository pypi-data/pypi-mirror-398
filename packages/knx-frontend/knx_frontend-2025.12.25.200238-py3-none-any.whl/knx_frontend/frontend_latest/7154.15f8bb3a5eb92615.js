export const __webpack_id__="7154";export const __webpack_ids__=["7154"];export const __webpack_modules__={23362:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),s=a(53289),n=a(96196),o=a(77845),r=a(92542),l=a(4657),d=a(39396),p=a(4848),h=(a(17963),a(89473)),c=a(32884),u=t([h,c]);[h,c]=u.then?(await u)():u;const _=t=>{if("object"!=typeof t||null===t)return!1;for(const e in t)if(Object.prototype.hasOwnProperty.call(t,e))return!1;return!0};class g extends n.WF{setValue(t){try{this._yaml=_(t)?"":(0,s.Bh)(t,{schema:this.yamlSchema,quotingType:'"',noRefs:!0})}catch(e){console.error(e,t),alert(`There was an error converting to YAML: ${e}`)}}firstUpdated(){void 0!==this.defaultValue&&this.setValue(this.defaultValue)}willUpdate(t){super.willUpdate(t),this.autoUpdate&&t.has("value")&&this.setValue(this.value)}focus(){this._codeEditor?.codemirror&&this._codeEditor?.codemirror.focus()}render(){return void 0===this._yaml?n.s6:n.qy`
      ${this.label?n.qy`<p>${this.label}${this.required?" *":""}</p>`:n.s6}
      <ha-code-editor
        .hass=${this.hass}
        .value=${this._yaml}
        .readOnly=${this.readOnly}
        .disableFullscreen=${this.disableFullscreen}
        mode="yaml"
        autocomplete-entities
        autocomplete-icons
        .error=${!1===this.isValid}
        @value-changed=${this._onChange}
        @blur=${this._onBlur}
        dir="ltr"
      ></ha-code-editor>
      ${this._showingError?n.qy`<ha-alert alert-type="error">${this._error}</ha-alert>`:n.s6}
      ${this.copyClipboard||this.hasExtraActions?n.qy`
            <div class="card-actions">
              ${this.copyClipboard?n.qy`
                    <ha-button appearance="plain" @click=${this._copyYaml}>
                      ${this.hass.localize("ui.components.yaml-editor.copy_to_clipboard")}
                    </ha-button>
                  `:n.s6}
              <slot name="extra-actions"></slot>
            </div>
          `:n.s6}
    `}_onChange(t){let e;t.stopPropagation(),this._yaml=t.detail.value;let a,i=!0;if(this._yaml)try{e=(0,s.Hh)(this._yaml,{schema:this.yamlSchema})}catch(n){i=!1,a=`${this.hass.localize("ui.components.yaml-editor.error",{reason:n.reason})}${n.mark?` (${this.hass.localize("ui.components.yaml-editor.error_location",{line:n.mark.line+1,column:n.mark.column+1})})`:""}`}else e={};this._error=a??"",i&&(this._showingError=!1),this.value=e,this.isValid=i,(0,r.r)(this,"value-changed",{value:e,isValid:i,errorMsg:a})}_onBlur(){this.showErrors&&this._error&&(this._showingError=!0)}get yaml(){return this._yaml}async _copyYaml(){this.yaml&&(await(0,l.l)(this.yaml),(0,p.P)(this,{message:this.hass.localize("ui.common.copied_clipboard")}))}static get styles(){return[d.RF,n.AH`
        .card-actions {
          border-radius: var(
            --actions-border-radius,
            var(--ha-border-radius-square) var(--ha-border-radius-square)
              var(--ha-card-border-radius, var(--ha-border-radius-lg))
              var(--ha-card-border-radius, var(--ha-border-radius-lg))
          );
          border: 1px solid var(--divider-color);
          padding: 5px 16px;
        }
        ha-code-editor {
          flex-grow: 1;
          min-height: 0;
        }
      `]}constructor(...t){super(...t),this.yamlSchema=s.my,this.isValid=!0,this.autoUpdate=!1,this.readOnly=!1,this.disableFullscreen=!1,this.required=!1,this.copyClipboard=!1,this.hasExtraActions=!1,this.showErrors=!0,this._yaml="",this._error="",this._showingError=!1}}(0,i.__decorate)([(0,o.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,i.__decorate)([(0,o.MZ)()],g.prototype,"value",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:!1})],g.prototype,"yamlSchema",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:!1})],g.prototype,"defaultValue",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"is-valid",type:Boolean})],g.prototype,"isValid",void 0),(0,i.__decorate)([(0,o.MZ)()],g.prototype,"label",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"auto-update",type:Boolean})],g.prototype,"autoUpdate",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"read-only",type:Boolean})],g.prototype,"readOnly",void 0),(0,i.__decorate)([(0,o.MZ)({type:Boolean,attribute:"disable-fullscreen"})],g.prototype,"disableFullscreen",void 0),(0,i.__decorate)([(0,o.MZ)({type:Boolean})],g.prototype,"required",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"copy-clipboard",type:Boolean})],g.prototype,"copyClipboard",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"has-extra-actions",type:Boolean})],g.prototype,"hasExtraActions",void 0),(0,i.__decorate)([(0,o.MZ)({attribute:"show-errors",type:Boolean})],g.prototype,"showErrors",void 0),(0,i.__decorate)([(0,o.wk)()],g.prototype,"_yaml",void 0),(0,i.__decorate)([(0,o.wk)()],g.prototype,"_error",void 0),(0,i.__decorate)([(0,o.wk)()],g.prototype,"_showingError",void 0),(0,i.__decorate)([(0,o.P)("ha-code-editor")],g.prototype,"_codeEditor",void 0),g=(0,i.__decorate)([(0,o.EM)("ha-yaml-editor")],g),e()}catch(_){e(_)}}))},40186:function(t,e,a){a.d(e,{a:()=>n});var i=a(92542);const s=()=>a.e("9469").then(a.bind(a,94764)),n=(t,e)=>{(0,i.r)(t,"show-dialog",{addHistory:!1,dialogTag:"dialog-tts-try",dialogImport:s,dialogParams:e})}},33104:function(t,e,a){var i=a(62826),s=a(96196),n=a(77845),o=a(22786);a(91120);class r extends s.WF{async focus(){await this.updateComplete;const t=this.renderRoot?.querySelector("ha-form");t?.focus()}render(){return s.qy`
      <div class="section">
        <div class="intro">
          <h3>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.config.title")}
          </h3>
          <p>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.config.description")}
          </p>
        </div>
        <ha-form
          .schema=${this._schema(this.supportedLanguages)}
          .data=${this.data}
          .hass=${this.hass}
          .computeLabel=${this._computeLabel}
        ></ha-form>
      </div>
    `}constructor(...t){super(...t),this._schema=(0,o.A)((t=>[{name:"",type:"grid",schema:[{name:"name",required:!0,selector:{text:{}}},t?{name:"language",required:!0,selector:{language:{languages:t}}}:{name:"",type:"constant"}]}])),this._computeLabel=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):""}}r.styles=s.AH`
    .section {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md);
      box-sizing: border-box;
      padding: 16px;
    }
    .intro {
      margin-bottom: 16px;
    }
    h3 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-normal);
      line-height: var(--ha-line-height-condensed);
      margin-top: 0;
      margin-bottom: 4px;
    }
    p {
      color: var(--secondary-text-color);
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      margin-top: 0;
      margin-bottom: 0;
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],r.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],r.prototype,"data",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1,type:Array})],r.prototype,"supportedLanguages",void 0),r=(0,i.__decorate)([(0,n.EM)("assist-pipeline-detail-config")],r)},3125:function(t,e,a){var i=a(62826),s=a(96196),n=a(77845),o=a(22786),r=a(92542);a(91120);class l extends s.WF{render(){return s.qy`
      <div class="section">
        <div class="intro">
          <h3>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.conversation.title")}
          </h3>
          <p>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.conversation.description")}
          </p>
        </div>
        <ha-form
          .schema=${this._schema(this.data?.conversation_engine,this.data?.language,this._supportedLanguages)}
          .data=${this.data}
          .hass=${this.hass}
          .computeLabel=${this._computeLabel}
          .computeHelper=${this._computeHelper}
          @supported-languages-changed=${this._supportedLanguagesChanged}
        ></ha-form>
      </div>
    `}_supportedLanguagesChanged(t){this._supportedLanguages=t.detail.value,"*"!==this._supportedLanguages&&this._supportedLanguages?.includes(this.data?.conversation_language||"")&&this.data?.conversation_language||setTimeout((()=>{const t={...this.data};"*"===this._supportedLanguages?t.conversation_language="*":t.conversation_language=this._supportedLanguages?.[0]??null,(0,r.r)(this,"value-changed",{value:t})}),0)}constructor(...t){super(...t),this._schema=(0,o.A)(((t,e,a)=>{const i=[{name:"",type:"grid",schema:[{name:"conversation_engine",required:!0,selector:{conversation_agent:{language:e}}}]}];return"*"!==a&&a?.length&&i[0].schema.push({name:"conversation_language",required:!0,selector:{language:{languages:a,no_sort:!0}}}),"conversation.home_assistant"!==t&&i.push({name:"prefer_local_intents",default:!0,selector:{boolean:{}}}),i})),this._computeLabel=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",this._computeHelper=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}_description`):""}}l.styles=s.AH`
    .section {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md);
      box-sizing: border-box;
      padding: 16px;
    }
    .intro {
      margin-bottom: 16px;
    }
    h3 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-normal);
      line-height: var(--ha-line-height-condensed);
      margin-top: 0;
      margin-bottom: 4px;
    }
    p {
      color: var(--secondary-text-color);
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      margin-top: 0;
      margin-bottom: 0;
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"data",void 0),(0,i.__decorate)([(0,n.wk)()],l.prototype,"_supportedLanguages",void 0),l=(0,i.__decorate)([(0,n.EM)("assist-pipeline-detail-conversation")],l)},96353:function(t,e,a){var i=a(62826),s=a(96196),n=a(77845),o=a(22786),r=a(92542);a(91120);class l extends s.WF{render(){return s.qy`
      <div class="section">
        <div class="intro">
          <h3>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.stt.title")}
          </h3>
          <p>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.stt.description")}
          </p>
        </div>
        <ha-form
          .schema=${this._schema(this.data?.language,this._supportedLanguages)}
          .data=${this.data}
          .hass=${this.hass}
          .computeLabel=${this._computeLabel}
          @supported-languages-changed=${this._supportedLanguagesChanged}
        ></ha-form>
      </div>
    `}_supportedLanguagesChanged(t){this._supportedLanguages=t.detail.value,this.data?.stt_language&&this._supportedLanguages?.includes(this.data.stt_language)||setTimeout((()=>{const t={...this.data};t.stt_language=this._supportedLanguages?.[0]??null,(0,r.r)(this,"value-changed",{value:t})}),0)}constructor(...t){super(...t),this._schema=(0,o.A)(((t,e)=>[{name:"",type:"grid",schema:[{name:"stt_engine",selector:{stt:{language:t}}},e?.length?{name:"stt_language",required:!0,selector:{language:{languages:e,no_sort:!0}}}:{name:"",type:"constant"}]}])),this._computeLabel=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):""}}l.styles=s.AH`
    .section {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md);
      box-sizing: border-box;
      padding: 16px;
    }
    .intro {
      margin-bottom: 16px;
    }
    h3 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-normal);
      line-height: var(--ha-line-height-condensed);
      margin-top: 0;
      margin-bottom: 4px;
    }
    p {
      color: var(--secondary-text-color);
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      margin-top: 0;
      margin-bottom: 0;
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"data",void 0),(0,i.__decorate)([(0,n.wk)()],l.prototype,"_supportedLanguages",void 0),l=(0,i.__decorate)([(0,n.EM)("assist-pipeline-detail-stt")],l)},11369:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),s=a(96196),n=a(77845),o=a(22786),r=a(92542),l=a(89473),d=(a(91120),a(40186)),p=t([l]);l=(p.then?(await p)():p)[0];class h extends s.WF{render(){return s.qy`
      <div class="section">
        <div class="content">
          <div class="intro">
          <h3>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.tts.title")}
          </h3>
          <p>
            ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.tts.description")}
          </p>
          </div>
          <ha-form
            .schema=${this._schema(this.data?.language,this._supportedLanguages)}
            .data=${this.data}
            .hass=${this.hass}
            .computeLabel=${this._computeLabel}
            @supported-languages-changed=${this._supportedLanguagesChanged}
          ></ha-form>
        </div>

       ${this.data?.tts_engine?s.qy`<div class="footer">
               <ha-button @click=${this._preview}>
                 ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.try_tts")}
               </ha-button>
             </div>`:s.s6}
        </div>
      </div>
    `}async _preview(){if(!this.data)return;const t=this.data.tts_engine,e=this.data.tts_language||void 0,a=this.data.tts_voice||void 0;t&&(0,d.a)(this,{engine:t,language:e,voice:a})}_supportedLanguagesChanged(t){this._supportedLanguages=t.detail.value,this.data?.tts_language&&this._supportedLanguages?.includes(this.data?.tts_language)||setTimeout((()=>{const t={...this.data};t.tts_language=this._supportedLanguages?.[0]??null,(0,r.r)(this,"value-changed",{value:t})}),0)}constructor(...t){super(...t),this._schema=(0,o.A)(((t,e)=>[{name:"",type:"grid",schema:[{name:"tts_engine",selector:{tts:{language:t}}},e?.length?{name:"tts_language",required:!0,selector:{language:{languages:e,no_sort:!0}}}:{name:"",type:"constant"},{name:"tts_voice",selector:{tts_voice:{}},context:{language:"tts_language",engineId:"tts_engine"},required:!0}]}])),this._computeLabel=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):""}}h.styles=s.AH`
    .section {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md);
    }
    .content {
      padding: 16px;
    }
    .intro {
      margin-bottom: 16px;
    }
    h3 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-normal);
      line-height: var(--ha-line-height-condensed);
      margin-top: 0;
      margin-bottom: 4px;
    }
    p {
      color: var(--secondary-text-color);
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      margin-top: 0;
      margin-bottom: 0;
    }
    .footer {
      border-top: 1px solid var(--divider-color);
      padding: 8px 16px;
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],h.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],h.prototype,"data",void 0),(0,i.__decorate)([(0,n.wk)()],h.prototype,"_supportedLanguages",void 0),h=(0,i.__decorate)([(0,n.EM)("assist-pipeline-detail-tts")],h),e()}catch(h){e(h)}}))},17687:function(t,e,a){var i=a(62826),s=a(96196),n=a(77845),o=a(22786),r=a(92542);a(91120);class l extends s.WF{willUpdate(t){t.has("data")&&t.get("data")?.wake_word_entity!==this.data?.wake_word_entity&&(t.get("data")?.wake_word_entity&&this.data?.wake_word_id&&(0,r.r)(this,"value-changed",{value:{...this.data,wake_word_id:void 0}}),this._fetchWakeWords())}render(){return s.qy`
      <div class="section">
        <div class="content">
          <div class="intro">
            <h3>
              ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.title")}
            </h3>
            <p>
              ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.description")}
            </p>
            <ha-alert alert-type="info">
              ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.note")}
            </ha-alert>
          </div>
          <ha-form
            .schema=${this._schema(this._wakeWords)}
            .data=${this.data}
            .hass=${this.hass}
            .computeLabel=${this._computeLabel}
          ></ha-form>
        </div>
      </div>
    `}async _fetchWakeWords(){if(this._wakeWords=void 0,!this.data?.wake_word_entity)return;const t=this.data.wake_word_entity,e=await(a=this.hass,i=t,a.callWS({type:"wake_word/info",entity_id:i}));var a,i;this.data.wake_word_entity===t&&(this._wakeWords=e.wake_words,!this.data||this.data?.wake_word_id&&this._wakeWords.some((t=>t.id===this.data.wake_word_id))||(0,r.r)(this,"value-changed",{value:{...this.data,wake_word_id:this._wakeWords[0]?.id}}))}constructor(...t){super(...t),this._schema=(0,o.A)((t=>[{name:"",type:"grid",schema:[{name:"wake_word_entity",selector:{entity:{domain:"wake_word"}}},t?.length?{name:"wake_word_id",required:!0,selector:{select:{mode:"dropdown",sort:!0,options:t.map((t=>({value:t.id,label:t.name})))}}}:{name:"",type:"constant"}]}])),this._computeLabel=t=>t.name?this.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):""}}l.styles=s.AH`
    .section {
      border: 1px solid var(--divider-color);
      border-radius: var(--ha-border-radius-md);
    }
    .content {
      padding: 16px;
    }
    .intro {
      margin-bottom: 16px;
    }
    h3 {
      font-size: var(--ha-font-size-xl);
      font-weight: var(--ha-font-weight-normal);
      line-height: var(--ha-line-height-condensed);
      margin-top: 0;
      margin-bottom: 4px;
    }
    p {
      color: var(--secondary-text-color);
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      margin-top: 0;
      margin-bottom: 0;
    }
    a {
      color: var(--primary-color);
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],l.prototype,"data",void 0),(0,i.__decorate)([(0,n.wk)()],l.prototype,"_wakeWords",void 0),l=(0,i.__decorate)([(0,n.EM)("assist-pipeline-detail-wakeword")],l)},63571:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),s=a(96196),n=a(77845),o=a(22786),r=a(45369),l=a(59705),d=t([l]);l=(d.then?(await d)():d)[0];class p extends s.WF{render(){const t=this._processEvents(this.events);return t?s.qy`
      <assist-render-pipeline-run
        .hass=${this.hass}
        .pipelineRun=${t}
        .chatLog=${this.chatLog}
      ></assist-render-pipeline-run>
    `:this.events.length?s.qy`<ha-alert alert-type="error"
            >${this.hass.localize("ui.panel.config.voice_assistants.debug.error.showing_run")}</ha-alert
          >
          <ha-card>
            <ha-expansion-panel>
              <span slot="header"
                >${this.hass.localize("ui.panel.config.voice_assistants.debug.raw")}</span
              >
              <pre>${JSON.stringify(this.events,null,2)}</pre>
            </ha-expansion-panel>
          </ha-card>`:s.qy`<ha-alert alert-type="warning"
        >${this.hass.localize("ui.panel.config.voice_assistants.debug.no_events")}</ha-alert
      >`}constructor(...t){super(...t),this._processEvents=(0,o.A)((t=>{let e;return t.forEach((t=>{e=(0,r.QC)(e,t)})),e}))}}(0,i.__decorate)([(0,n.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],p.prototype,"events",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],p.prototype,"chatLog",void 0),p=(0,i.__decorate)([(0,n.EM)("assist-render-pipeline-events")],p),e()}catch(p){e(p)}}))},59705:function(t,e,a){a.a(t,(async function(t,e){try{var i=a(62826),s=a(96196),n=a(77845),o=(a(95379),a(17963),a(89473)),r=a(89600),l=(a(34811),a(20679)),d=a(23362),p=a(10234),h=t([o,r,d,l]);[o,r,d,l]=h.then?(await h)():h;const c=["pipeline","language"],u=["engine"],_=["engine"],g=["engine","language","intent_input"],v=["engine","language","voice","tts_input"],m={ready:0,wake_word:1,stt:2,intent:3,tts:4,done:5,error:6},y=(t,e)=>t.init_options?m[t.init_options.start_stage]<=m[e]&&m[e]<=m[t.init_options.end_stage]:e in t,b=(t,e,a)=>"error"in t&&a===e?s.qy`
    <ha-alert alert-type="error">
      ${t.error.message} (${t.error.code})
    </ha-alert>
  `:"",f=(t,e,a,i="-start")=>{const n=e.events.find((t=>t.type===`${a}`+i)),o=e.events.find((t=>t.type===`${a}-end`));if(!n)return"";if(!o)return"error"in e?s.qy`❌`:s.qy` <ha-spinner size="small"></ha-spinner> `;const r=new Date(o.timestamp).getTime()-new Date(n.timestamp).getTime(),d=(0,l.ZV)(r/1e3,t.locale,{maximumFractionDigits:2});return s.qy`${d}s ✅`},w=(t,e,a)=>a.map((a=>{const i=t.localize(`ui.panel.config.voice_assistants.debug.stages.${a}`);return s.qy`
      <div class="row">
        <div>${i}</div>
        <div>${e[a]}</div>
      </div>
    `})),$=(t,e,a)=>{const i={};let n=!1;for(const s in e)a.includes(s)||"done"===s||(n=!0,i[s]=e[s]);return n?s.qy`<ha-expansion-panel class="yaml-expansion">
        <span slot="header"
          >${t.localize("ui.panel.config.voice_assistants.debug.raw")}</span
        >
        <ha-yaml-editor readOnly autoUpdate .value=${i}></ha-yaml-editor>
      </ha-expansion-panel>`:""};class x extends s.WF{get _isPlaying(){return null!=this._audioElement&&!this._audioElement.paused}render(){const t=this.pipelineRun&&["tts","intent","stt","wake_word"].find((t=>t in this.pipelineRun))||"ready";let e;if(this.chatLog)e=this.chatLog.content.filter(this.pipelineRun.finished?t=>"system"===t.role||t.created>=this.pipelineRun.started&&t.created<=this.pipelineRun.finished:t=>"system"===t.role||t.created>=this.pipelineRun.started);else{e=[];const t=(this.pipelineRun.init_options&&"text"in this.pipelineRun.init_options.input?this.pipelineRun.init_options.input.text:void 0)||this.pipelineRun?.stt?.stt_output?.text||this.pipelineRun?.intent?.intent_input;t&&e.push({role:"user",content:t}),this.pipelineRun?.intent?.intent_output?.response?.speech?.plain?.speech&&e.push({role:"assistant",content:this.pipelineRun.intent.intent_output.response.speech.plain.speech})}return s.qy`
      <ha-card>
        <div class="card-content">
          <div class="row heading">
            <div>
              ${this.hass.localize("ui.panel.config.voice_assistants.debug.run")}
            </div>
            <div>${this.pipelineRun.stage}</div>
          </div>

          ${w(this.hass,this.pipelineRun.run,c)}
          ${e.length>0?s.qy`
                <div class="messages">
                  ${e.map((t=>"system"===t.role?t.content?s.qy`
                            <ha-expansion-panel
                              class="content-expansion ${t.role}"
                            >
                              <div slot="header">System</div>
                              <pre>${t.content}</pre>
                            </ha-expansion-panel>
                          `:s.s6:"tool_result"===t.role?s.qy`
                            <ha-expansion-panel
                              class="content-expansion ${t.role}"
                            >
                              <div slot="header">
                                Result for ${t.tool_name}
                              </div>
                              <ha-yaml-editor
                                read-only
                                auto-update
                                .value=${t}
                              ></ha-yaml-editor>
                            </ha-expansion-panel>
                          `:s.qy`
                            ${t.content?s.qy`
                                  <div class=${`message ${t.role}`}>
                                    ${t.content}
                                  </div>
                                `:s.s6}
                            ${"assistant"===t.role&&t.tool_calls?.length?s.qy`
                                  <ha-expansion-panel
                                    class="content-expansion assistant"
                                  >
                                    <span slot="header">
                                      Call
                                      ${1===t.tool_calls.length?t.tool_calls[0].tool_name:`${t.tool_calls.length} tools`}
                                    </span>

                                    <ha-yaml-editor
                                      read-only
                                      auto-update
                                      .value=${t.tool_calls}
                                    ></ha-yaml-editor>
                                  </ha-expansion-panel>
                                `:s.s6}
                          `))}
                </div>
                <div style="clear:both"></div>
              `:""}
        </div>
      </ha-card>

      ${b(this.pipelineRun,"ready",t)}
      ${y(this.pipelineRun,"wake_word")?s.qy`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.wake_word")}</span
                  >
                  ${f(this.hass,this.pipelineRun,"wake_word")}
                </div>
                ${this.pipelineRun.wake_word?s.qy`
                      <div class="card-content">
                        ${w(this.hass,this.pipelineRun.wake_word,u)}
                        ${this.pipelineRun.wake_word.wake_word_output?s.qy`<div class="row">
                                <div>
                                  ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.model")}
                                </div>
                                <div>
                                  ${this.pipelineRun.wake_word.wake_word_output.ww_id}
                                </div>
                              </div>
                              <div class="row">
                                <div>
                                  ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.timestamp")}
                                </div>
                                <div>
                                  ${this.pipelineRun.wake_word.wake_word_output.timestamp}
                                </div>
                              </div>`:""}
                        ${$(this.hass,this.pipelineRun.wake_word,u)}
                      </div>
                    `:""}
              </div>
            </ha-card>
          `:""}
      ${b(this.pipelineRun,"wake_word",t)}
      ${y(this.pipelineRun,"stt")?s.qy`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.speech_to_text")}</span
                  >
                  ${f(this.hass,this.pipelineRun,"stt","-vad-end")}
                </div>
                ${this.pipelineRun.stt?s.qy`
                      <div class="card-content">
                        ${w(this.hass,this.pipelineRun.stt,_)}
                        <div class="row">
                          <div>
                            ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.language")}
                          </div>
                          <div>${this.pipelineRun.stt.metadata.language}</div>
                        </div>
                        ${this.pipelineRun.stt.stt_output?s.qy`<div class="row">
                              <div>
                                ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.output")}
                              </div>
                              <div>${this.pipelineRun.stt.stt_output.text}</div>
                            </div>`:""}
                        ${$(this.hass,this.pipelineRun.stt,_)}
                      </div>
                    `:""}
              </div>
            </ha-card>
          `:""}
      ${b(this.pipelineRun,"stt",t)}
      ${y(this.pipelineRun,"intent")?s.qy`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.natural_language_processing")}</span
                  >
                  ${f(this.hass,this.pipelineRun,"intent")}
                </div>
                ${this.pipelineRun.intent?s.qy`
                      <div class="card-content">
                        ${w(this.hass,this.pipelineRun.intent,g)}
                        ${this.pipelineRun.intent.intent_output?s.qy`<div class="row">
                                <div>
                                  ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.response_type")}
                                </div>
                                <div>
                                  ${this.pipelineRun.intent.intent_output.response.response_type}
                                </div>
                              </div>
                              ${"error"===this.pipelineRun.intent.intent_output.response.response_type?s.qy`<div class="row">
                                    <div>
                                      ${this.hass.localize("ui.panel.config.voice_assistants.debug.error.code")}
                                    </div>
                                    <div>
                                      ${this.pipelineRun.intent.intent_output.response.data.code}
                                    </div>
                                  </div>`:""}`:""}
                        <div class="row">
                          <div>
                            ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.prefer_local")}
                          </div>
                          <div>
                            ${this.pipelineRun.intent.prefer_local_intents}
                          </div>
                        </div>
                        <div class="row">
                          <div>
                            ${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.processed_locally")}
                          </div>
                          <div>
                            ${this.pipelineRun.intent.processed_locally}
                          </div>
                        </div>
                        ${$(this.hass,this.pipelineRun.intent,g)}
                      </div>
                    `:""}
              </div>
            </ha-card>
          `:""}
      ${b(this.pipelineRun,"intent",t)}
      ${y(this.pipelineRun,"tts")?s.qy`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${this.hass.localize("ui.panel.config.voice_assistants.debug.stages.text_to_speech")}</span
                  >
                  ${f(this.hass,this.pipelineRun,"tts")}
                </div>
                ${this.pipelineRun.tts?s.qy`
                      <div class="card-content">
                        ${w(this.hass,this.pipelineRun.tts,v)}
                        ${$(this.hass,this.pipelineRun.tts,v)}
                      </div>
                    `:""}
              </div>
              ${this.pipelineRun?.tts?.tts_output?s.qy`
                    <div class="card-actions">
                      <ha-button
                        .variant=${this._isPlaying?"danger":"brand"}
                        @click=${this._isPlaying?this._stopTTS:this._playTTS}
                      >
                        ${this._isPlaying?this.hass.localize("ui.panel.config.voice_assistants.debug.stop_audio"):this.hass.localize("ui.panel.config.voice_assistants.debug.play_audio")}
                      </ha-button>
                    </div>
                  `:""}
            </ha-card>
          `:""}
      ${b(this.pipelineRun,"tts",t)}
      <ha-card>
        <ha-expansion-panel class="yaml-expansion">
          <span slot="header"
            >${this.hass.localize("ui.panel.config.voice_assistants.debug.raw")}</span
          >
          <ha-yaml-editor
            read-only
            auto-update
            .value=${this.pipelineRun}
          ></ha-yaml-editor>
        </ha-expansion-panel>
      </ha-card>
    `}_playTTS(){this._stopTTS();const t=this.pipelineRun.tts.tts_output.url;this._audioElement=new Audio(t),this._audioElement.addEventListener("error",(()=>{(0,p.K$)(this,{title:this.hass.localize("ui.panel.config.voice_assistants.debug.error.title"),text:this.hass.localize("ui.panel.config.voice_assistants.debug.error.playing_audio")})})),this._audioElement.addEventListener("play",(()=>{this.requestUpdate()})),this._audioElement.addEventListener("ended",(()=>{this.requestUpdate()})),this._audioElement.addEventListener("canplaythrough",(()=>{this._audioElement.play()}))}_stopTTS(){this._audioElement&&(this._audioElement.pause(),this._audioElement.currentTime=0,this._audioElement=void 0,this.requestUpdate())}disconnectedCallback(){super.disconnectedCallback(),this._stopTTS()}}x.styles=s.AH`
    :host {
      display: block;
    }
    ha-card,
    ha-alert {
      display: block;
      margin-bottom: 16px;
    }
    .row {
      display: flex;
      justify-content: space-between;
    }
    .row > div:last-child {
      text-align: right;
    }
    .yaml-expansion {
      padding-left: 8px;
      padding-inline-start: 8px;
      padding-inline-end: initial;
    }
    .card-content .yaml-expansion {
      padding-left: 0px;
      padding-inline-start: 0px;
      padding-inline-end: initial;
      --expansion-panel-summary-padding: 0px;
      --expansion-panel-content-padding: 0px;
    }
    .heading {
      font-weight: var(--ha-font-weight-medium);
      margin-bottom: 16px;
    }

    .messages {
      margin-top: 8px;
    }

    .content-expansion {
      margin: 8px 0;
      border-radius: var(--ha-border-radius-xl);
      clear: both;
      padding: 0 8px;
      --input-fill-color: none;
      max-width: calc(100% - 24px);
      --expansion-panel-summary-padding: 0px;
      --expansion-panel-content-padding: 0px;
    }

    .content-expansion *[slot="header"] {
      font-weight: var(--ha-font-weight-normal);
    }

    .system {
      background-color: var(--success-color);
    }

    .message {
      padding: 8px;
    }

    .message,
    .content-expansion {
      font-size: var(--ha-font-size-l);
      margin: 8px 0;
      border-radius: var(--ha-border-radius-xl);
      clear: both;
    }

    .messages pre {
      white-space: pre-wrap;
    }

    .user,
    .tool_result {
      margin-left: 24px;
      margin-inline-start: 24px;
      margin-inline-end: initial;
      float: var(--float-end);
      border-bottom-right-radius: 0px;
      background-color: var(--light-primary-color);
      color: var(--text-light-primary-color, var(--primary-text-color));
      direction: var(--direction);
    }

    .message.user,
    .content-expansion div[slot="header"] {
      text-align: right;
    }

    .assistant {
      margin-right: 24px;
      margin-inline-end: 24px;
      margin-inline-start: initial;
      float: var(--float-start);
      border-bottom-left-radius: 0px;
      background-color: var(--primary-color);
      color: var(--text-primary-color);
      direction: var(--direction);
    }
  `,(0,i.__decorate)([(0,n.MZ)({attribute:!1})],x.prototype,"hass",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],x.prototype,"pipelineRun",void 0),(0,i.__decorate)([(0,n.MZ)({attribute:!1})],x.prototype,"chatLog",void 0),x=(0,i.__decorate)([(0,n.EM)("assist-render-pipeline-run")],x),e()}catch(c){e(c)}}))},67065:function(t,e,a){a.a(t,(async function(t,i){try{a.r(e),a.d(e,{DialogVoiceAssistantPipelineDetail:()=>b});var s=a(62826),n=a(96196),o=a(77845),r=a(22786),l=a(92542),d=a(55124),p=a(41144),h=a(89473),c=(a(86451),a(91120),a(56565),a(45369)),u=a(39396),_=(a(33104),a(3125),a(96353),a(11369)),g=(a(17687),a(63571)),v=t([h,_,g]);[h,_,g]=v.then?(await v)():v;const m="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",y="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z";class b extends n.WF{showDialog(t){if(this._params=t,this._error=void 0,this._cloudActive=this._params.cloudActiveSubscription,this._params.pipeline)return this._data={prefer_local_intents:!1,...this._params.pipeline},void(this._hideWakeWord=this._params.hideWakeWord||!this._data.wake_word_entity);let e,a;if(this._hideWakeWord=!0,this._cloudActive)for(const i of Object.values(this.hass.entities))if("cloud"===i.platform)if("stt"===(0,p.m)(i.entity_id)){if(e=i.entity_id,a)break}else if("tts"===(0,p.m)(i.entity_id)&&(a=i.entity_id,e))break;this._data={language:(this.hass.config.language||this.hass.locale.language).substring(0,2),stt_engine:e,tts_engine:a}}closeDialog(){this._params=void 0,this._data=void 0,this._hideWakeWord=!1,(0,l.r)(this,"dialog-closed",{dialog:this.localName})}firstUpdated(){this._getSupportedLanguages()}async _getSupportedLanguages(){const{languages:t}=await(0,c.ds)(this.hass);this._supportedLanguages=t}render(){if(!this._params||!this._data)return n.s6;const t=this._params.pipeline?.id?this._params.pipeline.name:this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_assistant_title");return n.qy`
      <ha-dialog
        open
        @closed=${this.closeDialog}
        scrimClickAction
        escapeKeyAction
        .heading=${t}
      >
        <ha-dialog-header slot="heading">
          <ha-icon-button
            slot="navigationIcon"
            dialogAction="cancel"
            .label=${this.hass.localize("ui.common.close")}
            .path=${m}
          ></ha-icon-button>
          <span slot="title" .title=${t}>${t}</span>
          ${this._hideWakeWord&&!this._params.hideWakeWord&&this._hasWakeWorkEntities(this.hass.states)?n.qy`<ha-button-menu
                slot="actionItems"
                @action=${this._handleShowWakeWord}
                @closed=${d.d}
                menu-corner="END"
                corner="BOTTOM_END"
              >
                <ha-icon-button
                  .path=${y}
                  slot="trigger"
                ></ha-icon-button>
                <ha-list-item>
                  ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_streaming_wake_word")}
                </ha-list-item></ha-button-menu
              >`:n.s6}
        </ha-dialog-header>
        <div class="content">
          ${this._error?n.qy`<ha-alert alert-type="error">${this._error}</ha-alert>`:n.s6}
          <assist-pipeline-detail-config
            .hass=${this.hass}
            .data=${this._data}
            .supportedLanguages=${this._supportedLanguages}
            keys="name,language"
            @value-changed=${this._valueChanged}
            ?dialogInitialFocus=${!this._params.pipeline?.id}
          ></assist-pipeline-detail-config>
          <assist-pipeline-detail-conversation
            .hass=${this.hass}
            .data=${this._data}
            keys="conversation_engine,conversation_language,prefer_local_intents"
            @value-changed=${this._valueChanged}
          ></assist-pipeline-detail-conversation>
          ${this._cloudActive||"cloud"!==this._data.tts_engine&&"cloud"!==this._data.stt_engine?n.s6:n.qy`
                <ha-alert alert-type="warning">
                  ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.no_cloud_message")}
                  <ha-button size="small" href="/config/cloud" slot="action">
                    ${this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.no_cloud_action")}
                  </ha-button>
                </ha-alert>
              `}
          <assist-pipeline-detail-stt
            .hass=${this.hass}
            .data=${this._data}
            keys="stt_engine,stt_language"
            @value-changed=${this._valueChanged}
          ></assist-pipeline-detail-stt>
          <assist-pipeline-detail-tts
            .hass=${this.hass}
            .data=${this._data}
            keys="tts_engine,tts_language,tts_voice"
            @value-changed=${this._valueChanged}
          ></assist-pipeline-detail-tts>
          ${this._hideWakeWord?n.s6:n.qy`<assist-pipeline-detail-wakeword
                .hass=${this.hass}
                .data=${this._data}
                keys="wake_word_entity,wake_word_id"
                @value-changed=${this._valueChanged}
              ></assist-pipeline-detail-wakeword>`}
        </div>
        <ha-button
          slot="primaryAction"
          @click=${this._updatePipeline}
          .loading=${this._submitting}
          dialogInitialFocus
        >
          ${this._params.pipeline?.id?this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.update_assistant_action"):this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_assistant_action")}
        </ha-button>
      </ha-dialog>
    `}_handleShowWakeWord(){this._hideWakeWord=!1}_valueChanged(t){this._error=void 0;const e={};t.currentTarget.getAttribute("keys").split(",").forEach((a=>{e[a]=t.detail.value[a]})),this._data={...this._data,...e}}async _updatePipeline(){this._submitting=!0;try{const t=this._data,e={name:t.name,language:t.language,conversation_engine:t.conversation_engine,conversation_language:t.conversation_language??null,prefer_local_intents:t.prefer_local_intents??!0,stt_engine:t.stt_engine??null,stt_language:t.stt_language??null,tts_engine:t.tts_engine??null,tts_language:t.tts_language??null,tts_voice:t.tts_voice??null,wake_word_entity:t.wake_word_entity??null,wake_word_id:t.wake_word_id??null};this._params.pipeline?.id?await this._params.updatePipeline(e):this._params.createPipeline?await this._params.createPipeline(e):console.error("No createPipeline function provided"),this.closeDialog()}catch(t){this._error=t?.message||"Unknown error"}finally{this._submitting=!1}}static get styles(){return[u.nA,n.AH`
        .content > *:not(:last-child) {
          margin-bottom: 16px;
          display: block;
        }
        ha-alert {
          margin-bottom: 16px;
          display: block;
        }
        a {
          text-decoration: none;
        }
      `]}constructor(...t){super(...t),this._hideWakeWord=!1,this._submitting=!1,this._hasWakeWorkEntities=(0,r.A)((t=>Object.keys(t).some((t=>t.startsWith("wake_word.")))))}}(0,s.__decorate)([(0,o.MZ)({attribute:!1})],b.prototype,"hass",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_params",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_data",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_hideWakeWord",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_cloudActive",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_error",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_submitting",void 0),(0,s.__decorate)([(0,o.wk)()],b.prototype,"_supportedLanguages",void 0),b=(0,s.__decorate)([(0,o.EM)("dialog-voice-assistant-pipeline-detail")],b),i()}catch(m){i(m)}}))}};
//# sourceMappingURL=7154.15f8bb3a5eb92615.js.map