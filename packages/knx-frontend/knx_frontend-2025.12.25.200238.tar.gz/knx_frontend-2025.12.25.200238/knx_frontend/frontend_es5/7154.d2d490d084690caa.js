"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["7154"],{23362:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(61397),s=a(50264),n=a(44734),o=a(56038),r=a(69683),l=a(6454),d=a(25460),p=(a(28706),a(62826)),c=a(53289),h=a(96196),u=a(77845),v=a(92542),g=a(4657),_=a(39396),m=a(4848),y=(a(17963),a(89473)),f=a(32884),b=e([y,f]);[y,f]=b.then?(await b)():b;var w,$,k,x,A,z,L=e=>e,q=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(i))).yamlSchema=c.my,e.isValid=!0,e.autoUpdate=!1,e.readOnly=!1,e.disableFullscreen=!1,e.required=!1,e.copyClipboard=!1,e.hasExtraActions=!1,e.showErrors=!0,e._yaml="",e._error="",e._showingError=!1,e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"setValue",value:function(e){try{this._yaml=(e=>{if("object"!=typeof e||null===e)return!1;for(var t in e)if(Object.prototype.hasOwnProperty.call(e,t))return!1;return!0})(e)?"":(0,c.Bh)(e,{schema:this.yamlSchema,quotingType:'"',noRefs:!0})}catch(t){console.error(t,e),alert(`There was an error converting to YAML: ${t}`)}}},{key:"firstUpdated",value:function(){void 0!==this.defaultValue&&this.setValue(this.defaultValue)}},{key:"willUpdate",value:function(e){(0,d.A)(t,"willUpdate",this,3)([e]),this.autoUpdate&&e.has("value")&&this.setValue(this.value)}},{key:"focus",value:function(){var e,t;null!==(e=this._codeEditor)&&void 0!==e&&e.codemirror&&(null===(t=this._codeEditor)||void 0===t||t.codemirror.focus())}},{key:"render",value:function(){return void 0===this._yaml?h.s6:(0,h.qy)(w||(w=L`
      ${0}
      <ha-code-editor
        .hass=${0}
        .value=${0}
        .readOnly=${0}
        .disableFullscreen=${0}
        mode="yaml"
        autocomplete-entities
        autocomplete-icons
        .error=${0}
        @value-changed=${0}
        @blur=${0}
        dir="ltr"
      ></ha-code-editor>
      ${0}
      ${0}
    `),this.label?(0,h.qy)($||($=L`<p>${0}${0}</p>`),this.label,this.required?" *":""):h.s6,this.hass,this._yaml,this.readOnly,this.disableFullscreen,!1===this.isValid,this._onChange,this._onBlur,this._showingError?(0,h.qy)(k||(k=L`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):h.s6,this.copyClipboard||this.hasExtraActions?(0,h.qy)(x||(x=L`
            <div class="card-actions">
              ${0}
              <slot name="extra-actions"></slot>
            </div>
          `),this.copyClipboard?(0,h.qy)(A||(A=L`
                    <ha-button appearance="plain" @click=${0}>
                      ${0}
                    </ha-button>
                  `),this._copyYaml,this.hass.localize("ui.components.yaml-editor.copy_to_clipboard")):h.s6):h.s6)}},{key:"_onChange",value:function(e){var t;e.stopPropagation(),this._yaml=e.detail.value;var a,i=!0;if(this._yaml)try{t=(0,c.Hh)(this._yaml,{schema:this.yamlSchema})}catch(s){i=!1,a=`${this.hass.localize("ui.components.yaml-editor.error",{reason:s.reason})}${s.mark?` (${this.hass.localize("ui.components.yaml-editor.error_location",{line:s.mark.line+1,column:s.mark.column+1})})`:""}`}else t={};this._error=null!=a?a:"",i&&(this._showingError=!1),this.value=t,this.isValid=i,(0,v.r)(this,"value-changed",{value:t,isValid:i,errorMsg:a})}},{key:"_onBlur",value:function(){this.showErrors&&this._error&&(this._showingError=!0)}},{key:"yaml",get:function(){return this._yaml}},{key:"_copyYaml",value:(a=(0,s.A)((0,i.A)().m((function e(){return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:if(!this.yaml){e.n=2;break}return e.n=1,(0,g.l)(this.yaml);case 1:(0,m.P)(this,{message:this.hass.localize("ui.common.copied_clipboard")});case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})}],[{key:"styles",get:function(){return[_.RF,(0,h.AH)(z||(z=L`
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
      `))]}}]);var a}(h.WF);(0,p.__decorate)([(0,u.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,p.__decorate)([(0,u.MZ)()],q.prototype,"value",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:!1})],q.prototype,"yamlSchema",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:!1})],q.prototype,"defaultValue",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"is-valid",type:Boolean})],q.prototype,"isValid",void 0),(0,p.__decorate)([(0,u.MZ)()],q.prototype,"label",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"auto-update",type:Boolean})],q.prototype,"autoUpdate",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"read-only",type:Boolean})],q.prototype,"readOnly",void 0),(0,p.__decorate)([(0,u.MZ)({type:Boolean,attribute:"disable-fullscreen"})],q.prototype,"disableFullscreen",void 0),(0,p.__decorate)([(0,u.MZ)({type:Boolean})],q.prototype,"required",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"copy-clipboard",type:Boolean})],q.prototype,"copyClipboard",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"has-extra-actions",type:Boolean})],q.prototype,"hasExtraActions",void 0),(0,p.__decorate)([(0,u.MZ)({attribute:"show-errors",type:Boolean})],q.prototype,"showErrors",void 0),(0,p.__decorate)([(0,u.wk)()],q.prototype,"_yaml",void 0),(0,p.__decorate)([(0,u.wk)()],q.prototype,"_error",void 0),(0,p.__decorate)([(0,u.wk)()],q.prototype,"_showingError",void 0),(0,p.__decorate)([(0,u.P)("ha-code-editor")],q.prototype,"_codeEditor",void 0),q=(0,p.__decorate)([(0,u.EM)("ha-yaml-editor")],q),t()}catch(R){t(R)}}))},40186:function(e,t,a){a.d(t,{a:function(){return n}});a(23792),a(26099),a(3362),a(62953);var i=a(92542),s=()=>a.e("9469").then(a.bind(a,94764)),n=(e,t)=>{(0,i.r)(e,"show-dialog",{addHistory:!1,dialogTag:"dialog-tts-try",dialogImport:s,dialogParams:t})}},33104:function(e,t,a){var i,s,n=a(61397),o=a(50264),r=a(44734),l=a(56038),d=a(69683),p=a(6454),c=(a(28706),a(62826)),h=a(96196),u=a(77845),v=a(22786),g=(a(91120),e=>e),_=function(e){function t(){var e;(0,r.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,d.A)(this,t,[].concat(i)))._schema=(0,v.A)((e=>[{name:"",type:"grid",schema:[{name:"name",required:!0,selector:{text:{}}},e?{name:"language",required:!0,selector:{language:{languages:e}}}:{name:"",type:"constant"}]}])),e._computeLabel=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",e}return(0,p.A)(t,e),(0,l.A)(t,[{key:"focus",value:(a=(0,o.A)((0,n.A)().m((function e(){var t,a;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,this.updateComplete;case 1:null==(a=null===(t=this.renderRoot)||void 0===t?void 0:t.querySelector("ha-form"))||a.focus();case 2:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"render",value:function(){return(0,h.qy)(i||(i=g`
      <div class="section">
        <div class="intro">
          <h3>
            ${0}
          </h3>
          <p>
            ${0}
          </p>
        </div>
        <ha-form
          .schema=${0}
          .data=${0}
          .hass=${0}
          .computeLabel=${0}
        ></ha-form>
      </div>
    `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.config.title"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.config.description"),this._schema(this.supportedLanguages),this.data,this.hass,this._computeLabel)}}]);var a}(h.WF);_.styles=(0,h.AH)(s||(s=g`
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
  `)),(0,c.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,c.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"data",void 0),(0,c.__decorate)([(0,u.MZ)({attribute:!1,type:Array})],_.prototype,"supportedLanguages",void 0),_=(0,c.__decorate)([(0,u.EM)("assist-pipeline-detail-config")],_)},3125:function(e,t,a){var i,s,n=a(44734),o=a(56038),r=a(69683),l=a(6454),d=(a(28706),a(74423),a(44114),a(62826)),p=a(96196),c=a(77845),h=a(22786),u=a(92542),v=(a(91120),e=>e),g=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(i)))._schema=(0,h.A)(((e,t,a)=>{var i=[{name:"",type:"grid",schema:[{name:"conversation_engine",required:!0,selector:{conversation_agent:{language:t}}}]}];return"*"!==a&&null!=a&&a.length&&i[0].schema.push({name:"conversation_language",required:!0,selector:{language:{languages:a,no_sort:!0}}}),"conversation.home_assistant"!==e&&i.push({name:"prefer_local_intents",default:!0,selector:{boolean:{}}}),i})),e._computeLabel=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",e._computeHelper=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}_description`):"",e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e,t;return(0,p.qy)(i||(i=v`
      <div class="section">
        <div class="intro">
          <h3>
            ${0}
          </h3>
          <p>
            ${0}
          </p>
        </div>
        <ha-form
          .schema=${0}
          .data=${0}
          .hass=${0}
          .computeLabel=${0}
          .computeHelper=${0}
          @supported-languages-changed=${0}
        ></ha-form>
      </div>
    `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.conversation.title"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.conversation.description"),this._schema(null===(e=this.data)||void 0===e?void 0:e.conversation_engine,null===(t=this.data)||void 0===t?void 0:t.language,this._supportedLanguages),this.data,this.hass,this._computeLabel,this._computeHelper,this._supportedLanguagesChanged)}},{key:"_supportedLanguagesChanged",value:function(e){var t,a,i;this._supportedLanguages=e.detail.value,"*"!==this._supportedLanguages&&null!==(t=this._supportedLanguages)&&void 0!==t&&t.includes((null===(a=this.data)||void 0===a?void 0:a.conversation_language)||"")&&null!==(i=this.data)&&void 0!==i&&i.conversation_language||setTimeout((()=>{var e,t,a=Object.assign({},this.data);"*"===this._supportedLanguages?a.conversation_language="*":a.conversation_language=null!==(e=null===(t=this._supportedLanguages)||void 0===t?void 0:t[0])&&void 0!==e?e:null;(0,u.r)(this,"value-changed",{value:a})}),0)}}])}(p.WF);g.styles=(0,p.AH)(s||(s=v`
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
  `)),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"data",void 0),(0,d.__decorate)([(0,c.wk)()],g.prototype,"_supportedLanguages",void 0),g=(0,d.__decorate)([(0,c.EM)("assist-pipeline-detail-conversation")],g)},96353:function(e,t,a){var i,s,n=a(44734),o=a(56038),r=a(69683),l=a(6454),d=(a(28706),a(74423),a(62826)),p=a(96196),c=a(77845),h=a(22786),u=a(92542),v=(a(91120),e=>e),g=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(i)))._schema=(0,h.A)(((e,t)=>[{name:"",type:"grid",schema:[{name:"stt_engine",selector:{stt:{language:e}}},null!=t&&t.length?{name:"stt_language",required:!0,selector:{language:{languages:t,no_sort:!0}}}:{name:"",type:"constant"}]}])),e._computeLabel=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e;return(0,p.qy)(i||(i=v`
      <div class="section">
        <div class="intro">
          <h3>
            ${0}
          </h3>
          <p>
            ${0}
          </p>
        </div>
        <ha-form
          .schema=${0}
          .data=${0}
          .hass=${0}
          .computeLabel=${0}
          @supported-languages-changed=${0}
        ></ha-form>
      </div>
    `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.stt.title"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.stt.description"),this._schema(null===(e=this.data)||void 0===e?void 0:e.language,this._supportedLanguages),this.data,this.hass,this._computeLabel,this._supportedLanguagesChanged)}},{key:"_supportedLanguagesChanged",value:function(e){var t,a;this._supportedLanguages=e.detail.value,null!==(t=this.data)&&void 0!==t&&t.stt_language&&null!==(a=this._supportedLanguages)&&void 0!==a&&a.includes(this.data.stt_language)||setTimeout((()=>{var e,t,a=Object.assign({},this.data);a.stt_language=null!==(e=null===(t=this._supportedLanguages)||void 0===t?void 0:t[0])&&void 0!==e?e:null,(0,u.r)(this,"value-changed",{value:a})}),0)}}])}(p.WF);g.styles=(0,p.AH)(s||(s=v`
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
  `)),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"data",void 0),(0,d.__decorate)([(0,c.wk)()],g.prototype,"_supportedLanguages",void 0),g=(0,d.__decorate)([(0,c.EM)("assist-pipeline-detail-stt")],g)},11369:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(61397),s=a(50264),n=a(44734),o=a(56038),r=a(69683),l=a(6454),d=(a(28706),a(74423),a(62826)),p=a(96196),c=a(77845),h=a(22786),u=a(92542),v=a(89473),g=(a(91120),a(40186)),_=e([v]);v=(_.then?(await _)():_)[0];var m,y,f,b=e=>e,w=function(e){function t(){var e;(0,n.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(i)))._schema=(0,h.A)(((e,t)=>[{name:"",type:"grid",schema:[{name:"tts_engine",selector:{tts:{language:e}}},null!=t&&t.length?{name:"tts_language",required:!0,selector:{language:{languages:t,no_sort:!0}}}:{name:"",type:"constant"},{name:"tts_voice",selector:{tts_voice:{}},context:{language:"tts_language",engineId:"tts_engine"},required:!0}]}])),e._computeLabel=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",e}return(0,l.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e,t;return(0,p.qy)(m||(m=b`
      <div class="section">
        <div class="content">
          <div class="intro">
          <h3>
            ${0}
          </h3>
          <p>
            ${0}
          </p>
          </div>
          <ha-form
            .schema=${0}
            .data=${0}
            .hass=${0}
            .computeLabel=${0}
            @supported-languages-changed=${0}
          ></ha-form>
        </div>

       ${0}
        </div>
      </div>
    `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.tts.title"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.tts.description"),this._schema(null===(e=this.data)||void 0===e?void 0:e.language,this._supportedLanguages),this.data,this.hass,this._computeLabel,this._supportedLanguagesChanged,null!==(t=this.data)&&void 0!==t&&t.tts_engine?(0,p.qy)(y||(y=b`<div class="footer">
               <ha-button @click=${0}>
                 ${0}
               </ha-button>
             </div>`),this._preview,this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.try_tts")):p.s6)}},{key:"_preview",value:(a=(0,s.A)((0,i.A)().m((function e(){var t,a,s;return(0,i.A)().w((function(e){for(;;)switch(e.n){case 0:if(this.data){e.n=1;break}return e.a(2);case 1:if(t=this.data.tts_engine,a=this.data.tts_language||void 0,s=this.data.tts_voice||void 0,t){e.n=2;break}return e.a(2);case 2:(0,g.a)(this,{engine:t,language:a,voice:s});case 3:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"_supportedLanguagesChanged",value:function(e){var t,a,i;this._supportedLanguages=e.detail.value,null!==(t=this.data)&&void 0!==t&&t.tts_language&&null!==(a=this._supportedLanguages)&&void 0!==a&&a.includes(null===(i=this.data)||void 0===i?void 0:i.tts_language)||setTimeout((()=>{var e,t,a=Object.assign({},this.data);a.tts_language=null!==(e=null===(t=this._supportedLanguages)||void 0===t?void 0:t[0])&&void 0!==e?e:null,(0,u.r)(this,"value-changed",{value:a})}),0)}}]);var a}(p.WF);w.styles=(0,p.AH)(f||(f=b`
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
  `)),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,d.__decorate)([(0,c.MZ)({attribute:!1})],w.prototype,"data",void 0),(0,d.__decorate)([(0,c.wk)()],w.prototype,"_supportedLanguages",void 0),w=(0,d.__decorate)([(0,c.EM)("assist-pipeline-detail-tts")],w),t()}catch($){t($)}}))},17687:function(e,t,a){var i,s,n=a(61397),o=a(50264),r=a(44734),l=a(56038),d=a(69683),p=a(6454),c=(a(28706),a(62062),a(18111),a(61701),a(13579),a(26099),a(62826)),h=a(96196),u=a(77845),v=a(22786),g=a(92542),_=(a(91120),e=>e),m=function(e){function t(){var e;(0,r.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,d.A)(this,t,[].concat(i)))._schema=(0,v.A)((e=>[{name:"",type:"grid",schema:[{name:"wake_word_entity",selector:{entity:{domain:"wake_word"}}},null!=e&&e.length?{name:"wake_word_id",required:!0,selector:{select:{mode:"dropdown",sort:!0,options:e.map((e=>({value:e.id,label:e.name})))}}}:{name:"",type:"constant"}]}])),e._computeLabel=t=>t.name?e.hass.localize(`ui.panel.config.voice_assistants.assistants.pipeline.detail.form.${t.name}`):"",e}return(0,p.A)(t,e),(0,l.A)(t,[{key:"willUpdate",value:function(e){var t,a,i,s;e.has("data")&&(null===(t=e.get("data"))||void 0===t?void 0:t.wake_word_entity)!==(null===(a=this.data)||void 0===a?void 0:a.wake_word_entity)&&(null!==(i=e.get("data"))&&void 0!==i&&i.wake_word_entity&&null!==(s=this.data)&&void 0!==s&&s.wake_word_id&&(0,g.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.data),{},{wake_word_id:void 0})}),this._fetchWakeWords())}},{key:"render",value:function(){return(0,h.qy)(i||(i=_`
      <div class="section">
        <div class="content">
          <div class="intro">
            <h3>
              ${0}
            </h3>
            <p>
              ${0}
            </p>
            <ha-alert alert-type="info">
              ${0}
            </ha-alert>
          </div>
          <ha-form
            .schema=${0}
            .data=${0}
            .hass=${0}
            .computeLabel=${0}
          ></ha-form>
        </div>
      </div>
    `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.title"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.description"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.steps.wakeword.note"),this._schema(this._wakeWords),this.data,this.hass,this._computeLabel)}},{key:"_fetchWakeWords",value:(a=(0,o.A)((0,n.A)().m((function e(){var t,a,i,s,o;return(0,n.A)().w((function(e){for(;;)switch(e.n){case 0:if(this._wakeWords=void 0,null!==(t=this.data)&&void 0!==t&&t.wake_word_entity){e.n=1;break}return e.a(2);case 1:return i=this.data.wake_word_entity,e.n=2,n=this.hass,r=i,n.callWS({type:"wake_word/info",entity_id:r});case 2:if(s=e.v,this.data.wake_word_entity===i){e.n=3;break}return e.a(2);case 3:this._wakeWords=s.wake_words,!this.data||null!==(a=this.data)&&void 0!==a&&a.wake_word_id&&this._wakeWords.some((e=>e.id===this.data.wake_word_id))||(0,g.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.data),{},{wake_word_id:null===(o=this._wakeWords[0])||void 0===o?void 0:o.id})});case 4:return e.a(2)}var n,r}),e,this)}))),function(){return a.apply(this,arguments)})}]);var a}(h.WF);m.styles=(0,h.AH)(s||(s=_`
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
  `)),(0,c.__decorate)([(0,u.MZ)({attribute:!1})],m.prototype,"hass",void 0),(0,c.__decorate)([(0,u.MZ)({attribute:!1})],m.prototype,"data",void 0),(0,c.__decorate)([(0,u.wk)()],m.prototype,"_wakeWords",void 0),m=(0,c.__decorate)([(0,u.EM)("assist-pipeline-detail-wakeword")],m)},63571:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(44734),s=a(56038),n=a(69683),o=a(6454),r=(a(28706),a(18111),a(7588),a(33110),a(26099),a(23500),a(62826)),l=a(96196),d=a(77845),p=a(22786),c=a(45369),h=a(59705),u=e([h]);h=(u.then?(await u)():u)[0];var v,g,_,m=e=>e,y=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,s=new Array(a),o=0;o<a;o++)s[o]=arguments[o];return(e=(0,n.A)(this,t,[].concat(s)))._processEvents=(0,p.A)((e=>{var t;return e.forEach((e=>{t=(0,c.QC)(t,e)})),t})),e}return(0,o.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){var e=this._processEvents(this.events);return e?(0,l.qy)(_||(_=m`
      <assist-render-pipeline-run
        .hass=${0}
        .pipelineRun=${0}
        .chatLog=${0}
      ></assist-render-pipeline-run>
    `),this.hass,e,this.chatLog):this.events.length?(0,l.qy)(v||(v=m`<ha-alert alert-type="error"
            >${0}</ha-alert
          >
          <ha-card>
            <ha-expansion-panel>
              <span slot="header"
                >${0}</span
              >
              <pre>${0}</pre>
            </ha-expansion-panel>
          </ha-card>`),this.hass.localize("ui.panel.config.voice_assistants.debug.error.showing_run"),this.hass.localize("ui.panel.config.voice_assistants.debug.raw"),JSON.stringify(this.events,null,2)):(0,l.qy)(g||(g=m`<ha-alert alert-type="warning"
        >${0}</ha-alert
      >`),this.hass.localize("ui.panel.config.voice_assistants.debug.no_events"))}}])}(l.WF);(0,r.__decorate)([(0,d.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,r.__decorate)([(0,d.MZ)({attribute:!1})],y.prototype,"events",void 0),(0,r.__decorate)([(0,d.MZ)({attribute:!1})],y.prototype,"chatLog",void 0),y=(0,r.__decorate)([(0,d.EM)("assist-render-pipeline-events")],y),t()}catch(f){t(f)}}))},59705:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(44734),s=a(56038),n=a(69683),o=a(25460),r=a(6454),l=(a(2008),a(50113),a(74423),a(62062),a(44114),a(18111),a(22489),a(20116),a(61701),a(26099),a(62826)),d=a(96196),p=a(77845),c=(a(95379),a(17963),a(89473)),h=a(89600),u=(a(34811),a(20679)),v=a(23362),g=a(10234),_=e([c,h,v,u]);[c,h,v,u]=_.then?(await _)():_;var m,y,f,b,w,$,k,x,A,z,L,q,R,W,E,M,Z,C,T,O,S,F,P,j,H,U,V,B=e=>e,D=["pipeline","language"],I=["engine"],N=["engine"],Y=["engine","language","intent_input"],K=["engine","language","voice","tts_input"],J={ready:0,wake_word:1,stt:2,intent:3,tts:4,done:5,error:6},Q=(e,t)=>e.init_options?J[e.init_options.start_stage]<=J[t]&&J[t]<=J[e.init_options.end_stage]:t in e,G=(e,t,a)=>"error"in e&&a===t?(0,d.qy)(m||(m=B`
    <ha-alert alert-type="error">
      ${0} (${0})
    </ha-alert>
  `),e.error.message,e.error.code):"",X=function(e,t,a){var i=arguments.length>3&&void 0!==arguments[3]?arguments[3]:"-start",s=t.events.find((e=>e.type===`${a}`+i)),n=t.events.find((e=>e.type===`${a}-end`));if(!s)return"";if(!n)return"error"in t?(0,d.qy)(y||(y=B`❌`)):(0,d.qy)(f||(f=B` <ha-spinner size="small"></ha-spinner> `));var o=new Date(n.timestamp).getTime()-new Date(s.timestamp).getTime(),r=(0,u.ZV)(o/1e3,e.locale,{maximumFractionDigits:2});return(0,d.qy)(b||(b=B`${0}s ✅`),r)},ee=(e,t,a)=>a.map((a=>{var i=e.localize(`ui.panel.config.voice_assistants.debug.stages.${a}`);return(0,d.qy)(w||(w=B`
      <div class="row">
        <div>${0}</div>
        <div>${0}</div>
      </div>
    `),i,t[a])})),te=(e,t,a)=>{var i={},s=!1;for(var n in t)a.includes(n)||"done"===n||(s=!0,i[n]=t[n]);return s?(0,d.qy)($||($=B`<ha-expansion-panel class="yaml-expansion">
        <span slot="header"
          >${0}</span
        >
        <ha-yaml-editor readOnly autoUpdate .value=${0}></ha-yaml-editor>
      </ha-expansion-panel>`),e.localize("ui.panel.config.voice_assistants.debug.raw"),i):""},ae=function(e){function t(){return(0,i.A)(this,t),(0,n.A)(this,t,arguments)}return(0,r.A)(t,e),(0,s.A)(t,[{key:"_isPlaying",get:function(){return null!=this._audioElement&&!this._audioElement.paused}},{key:"render",value:function(){var e,t,a=this.pipelineRun&&["tts","intent","stt","wake_word"].find((e=>e in this.pipelineRun))||"ready";if(this.chatLog)t=this.chatLog.content.filter(this.pipelineRun.finished?e=>"system"===e.role||e.created>=this.pipelineRun.started&&e.created<=this.pipelineRun.finished:e=>"system"===e.role||e.created>=this.pipelineRun.started);else{var i,s,n;t=[];var o=(this.pipelineRun.init_options&&"text"in this.pipelineRun.init_options.input?this.pipelineRun.init_options.input.text:void 0)||(null===(i=this.pipelineRun)||void 0===i||null===(i=i.stt)||void 0===i||null===(i=i.stt_output)||void 0===i?void 0:i.text)||(null===(s=this.pipelineRun)||void 0===s||null===(s=s.intent)||void 0===s?void 0:s.intent_input);o&&t.push({role:"user",content:o}),null!==(n=this.pipelineRun)&&void 0!==n&&null!==(n=n.intent)&&void 0!==n&&null!==(n=n.intent_output)&&void 0!==n&&null!==(n=n.response)&&void 0!==n&&null!==(n=n.speech)&&void 0!==n&&null!==(n=n.plain)&&void 0!==n&&n.speech&&t.push({role:"assistant",content:this.pipelineRun.intent.intent_output.response.speech.plain.speech})}return(0,d.qy)(k||(k=B`
      <ha-card>
        <div class="card-content">
          <div class="row heading">
            <div>
              ${0}
            </div>
            <div>${0}</div>
          </div>

          ${0}
          ${0}
        </div>
      </ha-card>

      ${0}
      ${0}
      ${0}
      ${0}
      ${0}
      ${0}
      ${0}
      ${0}
      ${0}
      <ha-card>
        <ha-expansion-panel class="yaml-expansion">
          <span slot="header"
            >${0}</span
          >
          <ha-yaml-editor
            read-only
            auto-update
            .value=${0}
          ></ha-yaml-editor>
        </ha-expansion-panel>
      </ha-card>
    `),this.hass.localize("ui.panel.config.voice_assistants.debug.run"),this.pipelineRun.stage,ee(this.hass,this.pipelineRun.run,D),t.length>0?(0,d.qy)(x||(x=B`
                <div class="messages">
                  ${0}
                </div>
                <div style="clear:both"></div>
              `),t.map((e=>{var t;return"system"===e.role?e.content?(0,d.qy)(A||(A=B`
                            <ha-expansion-panel
                              class="content-expansion ${0}"
                            >
                              <div slot="header">System</div>
                              <pre>${0}</pre>
                            </ha-expansion-panel>
                          `),e.role,e.content):d.s6:"tool_result"===e.role?(0,d.qy)(z||(z=B`
                            <ha-expansion-panel
                              class="content-expansion ${0}"
                            >
                              <div slot="header">
                                Result for ${0}
                              </div>
                              <ha-yaml-editor
                                read-only
                                auto-update
                                .value=${0}
                              ></ha-yaml-editor>
                            </ha-expansion-panel>
                          `),e.role,e.tool_name,e):(0,d.qy)(L||(L=B`
                            ${0}
                            ${0}
                          `),e.content?(0,d.qy)(q||(q=B`
                                  <div class=${0}>
                                    ${0}
                                  </div>
                                `),`message ${e.role}`,e.content):d.s6,"assistant"===e.role&&null!==(t=e.tool_calls)&&void 0!==t&&t.length?(0,d.qy)(R||(R=B`
                                  <ha-expansion-panel
                                    class="content-expansion assistant"
                                  >
                                    <span slot="header">
                                      Call
                                      ${0}
                                    </span>

                                    <ha-yaml-editor
                                      read-only
                                      auto-update
                                      .value=${0}
                                    ></ha-yaml-editor>
                                  </ha-expansion-panel>
                                `),1===e.tool_calls.length?e.tool_calls[0].tool_name:`${e.tool_calls.length} tools`,e.tool_calls):d.s6)}))):"",G(this.pipelineRun,"ready",a),Q(this.pipelineRun,"wake_word")?(0,d.qy)(W||(W=B`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${0}</span
                  >
                  ${0}
                </div>
                ${0}
              </div>
            </ha-card>
          `),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.wake_word"),X(this.hass,this.pipelineRun,"wake_word"),this.pipelineRun.wake_word?(0,d.qy)(E||(E=B`
                      <div class="card-content">
                        ${0}
                        ${0}
                        ${0}
                      </div>
                    `),ee(this.hass,this.pipelineRun.wake_word,I),this.pipelineRun.wake_word.wake_word_output?(0,d.qy)(M||(M=B`<div class="row">
                                <div>
                                  ${0}
                                </div>
                                <div>
                                  ${0}
                                </div>
                              </div>
                              <div class="row">
                                <div>
                                  ${0}
                                </div>
                                <div>
                                  ${0}
                                </div>
                              </div>`),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.model"),this.pipelineRun.wake_word.wake_word_output.ww_id,this.hass.localize("ui.panel.config.voice_assistants.debug.stages.timestamp"),this.pipelineRun.wake_word.wake_word_output.timestamp):"",te(this.hass,this.pipelineRun.wake_word,I)):""):"",G(this.pipelineRun,"wake_word",a),Q(this.pipelineRun,"stt")?(0,d.qy)(Z||(Z=B`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${0}</span
                  >
                  ${0}
                </div>
                ${0}
              </div>
            </ha-card>
          `),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.speech_to_text"),X(this.hass,this.pipelineRun,"stt","-vad-end"),this.pipelineRun.stt?(0,d.qy)(C||(C=B`
                      <div class="card-content">
                        ${0}
                        <div class="row">
                          <div>
                            ${0}
                          </div>
                          <div>${0}</div>
                        </div>
                        ${0}
                        ${0}
                      </div>
                    `),ee(this.hass,this.pipelineRun.stt,N),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.language"),this.pipelineRun.stt.metadata.language,this.pipelineRun.stt.stt_output?(0,d.qy)(T||(T=B`<div class="row">
                              <div>
                                ${0}
                              </div>
                              <div>${0}</div>
                            </div>`),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.output"),this.pipelineRun.stt.stt_output.text):"",te(this.hass,this.pipelineRun.stt,N)):""):"",G(this.pipelineRun,"stt",a),Q(this.pipelineRun,"intent")?(0,d.qy)(O||(O=B`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${0}</span
                  >
                  ${0}
                </div>
                ${0}
              </div>
            </ha-card>
          `),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.natural_language_processing"),X(this.hass,this.pipelineRun,"intent"),this.pipelineRun.intent?(0,d.qy)(S||(S=B`
                      <div class="card-content">
                        ${0}
                        ${0}
                        <div class="row">
                          <div>
                            ${0}
                          </div>
                          <div>
                            ${0}
                          </div>
                        </div>
                        <div class="row">
                          <div>
                            ${0}
                          </div>
                          <div>
                            ${0}
                          </div>
                        </div>
                        ${0}
                      </div>
                    `),ee(this.hass,this.pipelineRun.intent,Y),this.pipelineRun.intent.intent_output?(0,d.qy)(F||(F=B`<div class="row">
                                <div>
                                  ${0}
                                </div>
                                <div>
                                  ${0}
                                </div>
                              </div>
                              ${0}`),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.response_type"),this.pipelineRun.intent.intent_output.response.response_type,"error"===this.pipelineRun.intent.intent_output.response.response_type?(0,d.qy)(P||(P=B`<div class="row">
                                    <div>
                                      ${0}
                                    </div>
                                    <div>
                                      ${0}
                                    </div>
                                  </div>`),this.hass.localize("ui.panel.config.voice_assistants.debug.error.code"),this.pipelineRun.intent.intent_output.response.data.code):""):"",this.hass.localize("ui.panel.config.voice_assistants.debug.stages.prefer_local"),this.pipelineRun.intent.prefer_local_intents,this.hass.localize("ui.panel.config.voice_assistants.debug.stages.processed_locally"),this.pipelineRun.intent.processed_locally,te(this.hass,this.pipelineRun.intent,Y)):""):"",G(this.pipelineRun,"intent",a),Q(this.pipelineRun,"tts")?(0,d.qy)(j||(j=B`
            <ha-card>
              <div class="card-content">
                <div class="row heading">
                  <span
                    >${0}</span
                  >
                  ${0}
                </div>
                ${0}
              </div>
              ${0}
            </ha-card>
          `),this.hass.localize("ui.panel.config.voice_assistants.debug.stages.text_to_speech"),X(this.hass,this.pipelineRun,"tts"),this.pipelineRun.tts?(0,d.qy)(H||(H=B`
                      <div class="card-content">
                        ${0}
                        ${0}
                      </div>
                    `),ee(this.hass,this.pipelineRun.tts,K),te(this.hass,this.pipelineRun.tts,K)):"",null!==(e=this.pipelineRun)&&void 0!==e&&null!==(e=e.tts)&&void 0!==e&&e.tts_output?(0,d.qy)(U||(U=B`
                    <div class="card-actions">
                      <ha-button
                        .variant=${0}
                        @click=${0}
                      >
                        ${0}
                      </ha-button>
                    </div>
                  `),this._isPlaying?"danger":"brand",this._isPlaying?this._stopTTS:this._playTTS,this._isPlaying?this.hass.localize("ui.panel.config.voice_assistants.debug.stop_audio"):this.hass.localize("ui.panel.config.voice_assistants.debug.play_audio")):""):"",G(this.pipelineRun,"tts",a),this.hass.localize("ui.panel.config.voice_assistants.debug.raw"),this.pipelineRun)}},{key:"_playTTS",value:function(){this._stopTTS();var e=this.pipelineRun.tts.tts_output.url;this._audioElement=new Audio(e),this._audioElement.addEventListener("error",(()=>{(0,g.K$)(this,{title:this.hass.localize("ui.panel.config.voice_assistants.debug.error.title"),text:this.hass.localize("ui.panel.config.voice_assistants.debug.error.playing_audio")})})),this._audioElement.addEventListener("play",(()=>{this.requestUpdate()})),this._audioElement.addEventListener("ended",(()=>{this.requestUpdate()})),this._audioElement.addEventListener("canplaythrough",(()=>{this._audioElement.play()}))}},{key:"_stopTTS",value:function(){this._audioElement&&(this._audioElement.pause(),this._audioElement.currentTime=0,this._audioElement=void 0,this.requestUpdate())}},{key:"disconnectedCallback",value:function(){(0,o.A)(t,"disconnectedCallback",this,3)([]),this._stopTTS()}}])}(d.WF);ae.styles=(0,d.AH)(V||(V=B`
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
  `)),(0,l.__decorate)([(0,p.MZ)({attribute:!1})],ae.prototype,"hass",void 0),(0,l.__decorate)([(0,p.MZ)({attribute:!1})],ae.prototype,"pipelineRun",void 0),(0,l.__decorate)([(0,p.MZ)({attribute:!1})],ae.prototype,"chatLog",void 0),ae=(0,l.__decorate)([(0,p.EM)("assist-render-pipeline-run")],ae),t()}catch(ie){t(ie)}}))},67065:function(e,t,a){a.a(e,(async function(e,i){try{a.r(t),a.d(t,{DialogVoiceAssistantPipelineDetail:function(){return W}});var s=a(61397),n=a(50264),o=a(44734),r=a(56038),l=a(69683),d=a(6454),p=(a(28706),a(18111),a(7588),a(13579),a(26099),a(16034),a(23500),a(62826)),c=a(96196),h=a(77845),u=a(22786),v=a(92542),g=a(55124),_=a(41144),m=a(89473),y=(a(86451),a(91120),a(56565),a(45369)),f=a(39396),b=(a(33104),a(3125),a(96353),a(11369)),w=(a(17687),a(63571)),$=e([m,b,w]);[m,b,w]=$.then?(await $)():$;var k,x,A,z,L,q,R=e=>e,W=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,i=new Array(a),s=0;s<a;s++)i[s]=arguments[s];return(e=(0,l.A)(this,t,[].concat(i)))._hideWakeWord=!1,e._submitting=!1,e._hasWakeWorkEntities=(0,u.A)((e=>Object.keys(e).some((e=>e.startsWith("wake_word."))))),e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"showDialog",value:function(e){if(this._params=e,this._error=void 0,this._cloudActive=this._params.cloudActiveSubscription,this._params.pipeline)return this._data=Object.assign({prefer_local_intents:!1},this._params.pipeline),void(this._hideWakeWord=this._params.hideWakeWord||!this._data.wake_word_entity);var t,a;if(this._hideWakeWord=!0,this._cloudActive)for(var i=0,s=Object.values(this.hass.entities);i<s.length;i++){var n=s[i];if("cloud"===n.platform)if("stt"===(0,_.m)(n.entity_id)){if(t=n.entity_id,a)break}else if("tts"===(0,_.m)(n.entity_id)&&(a=n.entity_id,t))break}this._data={language:(this.hass.config.language||this.hass.locale.language).substring(0,2),stt_engine:t,tts_engine:a}}},{key:"closeDialog",value:function(){this._params=void 0,this._data=void 0,this._hideWakeWord=!1,(0,v.r)(this,"dialog-closed",{dialog:this.localName})}},{key:"firstUpdated",value:function(){this._getSupportedLanguages()}},{key:"_getSupportedLanguages",value:(i=(0,n.A)((0,s.A)().m((function e(){var t,a;return(0,s.A)().w((function(e){for(;;)switch(e.n){case 0:return e.n=1,(0,y.ds)(this.hass);case 1:t=e.v,a=t.languages,this._supportedLanguages=a;case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"render",value:function(){var e,t,a;if(!this._params||!this._data)return c.s6;var i=null!==(e=this._params.pipeline)&&void 0!==e&&e.id?this._params.pipeline.name:this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_assistant_title");return(0,c.qy)(k||(k=R`
      <ha-dialog
        open
        @closed=${0}
        scrimClickAction
        escapeKeyAction
        .heading=${0}
      >
        <ha-dialog-header slot="heading">
          <ha-icon-button
            slot="navigationIcon"
            dialogAction="cancel"
            .label=${0}
            .path=${0}
          ></ha-icon-button>
          <span slot="title" .title=${0}>${0}</span>
          ${0}
        </ha-dialog-header>
        <div class="content">
          ${0}
          <assist-pipeline-detail-config
            .hass=${0}
            .data=${0}
            .supportedLanguages=${0}
            keys="name,language"
            @value-changed=${0}
            ?dialogInitialFocus=${0}
          ></assist-pipeline-detail-config>
          <assist-pipeline-detail-conversation
            .hass=${0}
            .data=${0}
            keys="conversation_engine,conversation_language,prefer_local_intents"
            @value-changed=${0}
          ></assist-pipeline-detail-conversation>
          ${0}
          <assist-pipeline-detail-stt
            .hass=${0}
            .data=${0}
            keys="stt_engine,stt_language"
            @value-changed=${0}
          ></assist-pipeline-detail-stt>
          <assist-pipeline-detail-tts
            .hass=${0}
            .data=${0}
            keys="tts_engine,tts_language,tts_voice"
            @value-changed=${0}
          ></assist-pipeline-detail-tts>
          ${0}
        </div>
        <ha-button
          slot="primaryAction"
          @click=${0}
          .loading=${0}
          dialogInitialFocus
        >
          ${0}
        </ha-button>
      </ha-dialog>
    `),this.closeDialog,i,this.hass.localize("ui.common.close"),"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z",i,i,this._hideWakeWord&&!this._params.hideWakeWord&&this._hasWakeWorkEntities(this.hass.states)?(0,c.qy)(x||(x=R`<ha-button-menu
                slot="actionItems"
                @action=${0}
                @closed=${0}
                menu-corner="END"
                corner="BOTTOM_END"
              >
                <ha-icon-button
                  .path=${0}
                  slot="trigger"
                ></ha-icon-button>
                <ha-list-item>
                  ${0}
                </ha-list-item></ha-button-menu
              >`),this._handleShowWakeWord,g.d,"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_streaming_wake_word")):c.s6,this._error?(0,c.qy)(A||(A=R`<ha-alert alert-type="error">${0}</ha-alert>`),this._error):c.s6,this.hass,this._data,this._supportedLanguages,this._valueChanged,!(null!==(t=this._params.pipeline)&&void 0!==t&&t.id),this.hass,this._data,this._valueChanged,this._cloudActive||"cloud"!==this._data.tts_engine&&"cloud"!==this._data.stt_engine?c.s6:(0,c.qy)(z||(z=R`
                <ha-alert alert-type="warning">
                  ${0}
                  <ha-button size="small" href="/config/cloud" slot="action">
                    ${0}
                  </ha-button>
                </ha-alert>
              `),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.no_cloud_message"),this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.no_cloud_action")),this.hass,this._data,this._valueChanged,this.hass,this._data,this._valueChanged,this._hideWakeWord?c.s6:(0,c.qy)(L||(L=R`<assist-pipeline-detail-wakeword
                .hass=${0}
                .data=${0}
                keys="wake_word_entity,wake_word_id"
                @value-changed=${0}
              ></assist-pipeline-detail-wakeword>`),this.hass,this._data,this._valueChanged),this._updatePipeline,this._submitting,null!==(a=this._params.pipeline)&&void 0!==a&&a.id?this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.update_assistant_action"):this.hass.localize("ui.panel.config.voice_assistants.assistants.pipeline.detail.add_assistant_action"))}},{key:"_handleShowWakeWord",value:function(){this._hideWakeWord=!1}},{key:"_valueChanged",value:function(e){this._error=void 0;var t={};e.currentTarget.getAttribute("keys").split(",").forEach((a=>{t[a]=e.detail.value[a]})),this._data=Object.assign(Object.assign({},this._data),t)}},{key:"_updatePipeline",value:(a=(0,n.A)((0,s.A)().m((function e(){var t,a,i,n,o,r,l,d,p,c,h,u,v;return(0,s.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(this._submitting=!0,e.p=1,h=this._data,u={name:h.name,language:h.language,conversation_engine:h.conversation_engine,conversation_language:null!==(t=h.conversation_language)&&void 0!==t?t:null,prefer_local_intents:null===(a=h.prefer_local_intents)||void 0===a||a,stt_engine:null!==(i=h.stt_engine)&&void 0!==i?i:null,stt_language:null!==(n=h.stt_language)&&void 0!==n?n:null,tts_engine:null!==(o=h.tts_engine)&&void 0!==o?o:null,tts_language:null!==(r=h.tts_language)&&void 0!==r?r:null,tts_voice:null!==(l=h.tts_voice)&&void 0!==l?l:null,wake_word_entity:null!==(d=h.wake_word_entity)&&void 0!==d?d:null,wake_word_id:null!==(p=h.wake_word_id)&&void 0!==p?p:null},null===(c=this._params.pipeline)||void 0===c||!c.id){e.n=3;break}return e.n=2,this._params.updatePipeline(u);case 2:e.n=6;break;case 3:if(!this._params.createPipeline){e.n=5;break}return e.n=4,this._params.createPipeline(u);case 4:e.n=6;break;case 5:console.error("No createPipeline function provided");case 6:this.closeDialog(),e.n=8;break;case 7:e.p=7,v=e.v,this._error=(null==v?void 0:v.message)||"Unknown error";case 8:return e.p=8,this._submitting=!1,e.f(8);case 9:return e.a(2)}}),e,this,[[1,7,8,9]])}))),function(){return a.apply(this,arguments)})}],[{key:"styles",get:function(){return[f.nA,(0,c.AH)(q||(q=R`
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
      `))]}}]);var a,i}(c.WF);(0,p.__decorate)([(0,h.MZ)({attribute:!1})],W.prototype,"hass",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_params",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_data",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_hideWakeWord",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_cloudActive",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_error",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_submitting",void 0),(0,p.__decorate)([(0,h.wk)()],W.prototype,"_supportedLanguages",void 0),W=(0,p.__decorate)([(0,h.EM)("dialog-voice-assistant-pipeline-detail")],W),i()}catch(E){i(E)}}))}}]);
//# sourceMappingURL=7154.d2d490d084690caa.js.map