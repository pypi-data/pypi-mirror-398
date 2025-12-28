"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["1283"],{31747:function(e,t,a){a.a(e,(async function(e,i){try{a.d(t,{T:function(){return l}});var o=a(22),n=a(22786),r=e([o]);o=(r.then?(await r)():r)[0];var l=(e,t)=>{try{var a,i;return null!==(a=null===(i=s(t))||void 0===i?void 0:i.of(e))&&void 0!==a?a:e}catch(o){return e}},s=(0,n.A)((e=>new Intl.DisplayNames(e.language,{type:"language",fallback:"code"})));i()}catch(u){i(u)}}))},51362:function(e,t,a){a.a(e,(async function(e,i){try{a.d(t,{t:function(){return L}});var o=a(44734),n=a(56038),r=a(69683),l=a(6454),s=a(25460),u=a(22),c=(a(28706),a(50113),a(62062),a(26910),a(18111),a(20116),a(61701),a(26099),a(62826)),d=a(96196),h=a(77845),v=a(22786),p=a(92542),g=a(31747),_=a(25749),y=a(13673),f=a(89473),b=a(96943),m=e([u,f,b,g]);[u,f,b,g]=m.then?(await m)():m;var k,w,A,$,M,Z,q=e=>e,L=(e,t,a,i)=>{var o=[];if(t){var n=y.P.translations;o=e.map((e=>{var t,a=null===(t=n[e])||void 0===t?void 0:t.nativeName;if(!a)try{a=new Intl.DisplayNames(e,{type:"language",fallback:"code"}).of(e)}catch(i){a=e}return{id:e,primary:a,search_labels:[a]}}))}else i&&(o=e.map((e=>({id:e,primary:(0,g.T)(e,i),search_labels:[(0,g.T)(e,i)]}))));return!a&&i&&o.sort(((e,t)=>(0,_.SH)(e.primary,t.primary,i.language))),o},N=function(e){function t(){var e;(0,o.A)(this,t);for(var a=arguments.length,i=new Array(a),n=0;n<a;n++)i[n]=arguments[n];return(e=(0,r.A)(this,t,[].concat(i))).disabled=!1,e.required=!1,e.nativeName=!1,e.buttonStyle=!1,e.noSort=!1,e.inlineArrow=!1,e._defaultLanguages=[],e._getLanguagesOptions=(0,v.A)(L),e._getItems=()=>{var t,a;return e._getLanguagesOptions(null!==(t=e.languages)&&void 0!==t?t:e._defaultLanguages,e.nativeName,e.noSort,null===(a=e.hass)||void 0===a?void 0:a.locale)},e._getLanguageName=t=>{var a;return null===(a=e._getItems().find((e=>e.id===t)))||void 0===a?void 0:a.primary},e._valueRenderer=t=>{var a;return(0,d.qy)(k||(k=q`<span slot="headline"
      >${0}</span
    > `),null!==(a=e._getLanguageName(t))&&void 0!==a?a:t)},e._notFoundLabel=t=>{var a=(0,d.qy)(w||(w=q`<b>‘${0}’</b>`),t);return e.hass?e.hass.localize("ui.components.language-picker.no_match",{term:a}):(0,d.qy)(A||(A=q`No languages found for ${0}`),a)},e}return(0,l.A)(t,e),(0,n.A)(t,[{key:"firstUpdated",value:function(e){(0,s.A)(t,"firstUpdated",this,3)([e]),this._computeDefaultLanguageOptions()}},{key:"_computeDefaultLanguageOptions",value:function(){this._defaultLanguages=Object.keys(y.P.translations)}},{key:"render",value:function(){var e,t,a,i,o=null!==(e=this.value)&&void 0!==e?e:this.required&&!this.disabled?this._getItems()[0].id:this.value;return(0,d.qy)($||($=q`
      <ha-generic-picker
        .hass=${0}
        .autofocus=${0}
        popover-placement="bottom-end"
        .notFoundLabel=${0}
        .emptyLabel=${0}
        .placeholder=${0}
        .value=${0}
        .valueRenderer=${0}
        .disabled=${0}
        .helper=${0}
        .getItems=${0}
        @value-changed=${0}
        hide-clear-icon
      >
        ${0}
      </ha-generic-picker>
    `),this.hass,this.autofocus,this._notFoundLabel,(null===(t=this.hass)||void 0===t?void 0:t.localize("ui.components.language-picker.no_languages"))||"No languages available",null!==(a=this.label)&&void 0!==a?a:(null===(i=this.hass)||void 0===i?void 0:i.localize("ui.components.language-picker.language"))||"Language",o,this._valueRenderer,this.disabled,this.helper,this._getItems,this._changed,this.buttonStyle?(0,d.qy)(M||(M=q`<ha-button
              slot="field"
              .disabled=${0}
              @click=${0}
              appearance="plain"
              variant="neutral"
            >
              ${0}
              <ha-svg-icon slot="end" .path=${0}></ha-svg-icon>
            </ha-button>`),this.disabled,this._openPicker,this._getLanguageName(o),"M7,10L12,15L17,10H7Z"):d.s6)}},{key:"_openPicker",value:function(e){e.stopPropagation(),this.genericPicker.open()}},{key:"_changed",value:function(e){e.stopPropagation(),this.value=e.detail.value,(0,p.r)(this,"value-changed",{value:this.value})}}])}(d.WF);N.styles=(0,d.AH)(Z||(Z=q`
    ha-generic-picker {
      width: 100%;
      min-width: 200px;
      display: block;
    }
  `)),(0,c.__decorate)([(0,h.MZ)()],N.prototype,"value",void 0),(0,c.__decorate)([(0,h.MZ)()],N.prototype,"label",void 0),(0,c.__decorate)([(0,h.MZ)({type:Array})],N.prototype,"languages",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],N.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,reflect:!0})],N.prototype,"disabled",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],N.prototype,"required",void 0),(0,c.__decorate)([(0,h.MZ)()],N.prototype,"helper",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:"native-name",type:Boolean})],N.prototype,"nativeName",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"button-style"})],N.prototype,"buttonStyle",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:"no-sort",type:Boolean})],N.prototype,"noSort",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:"inline-arrow",type:Boolean})],N.prototype,"inlineArrow",void 0),(0,c.__decorate)([(0,h.wk)()],N.prototype,"_defaultLanguages",void 0),(0,c.__decorate)([(0,h.P)("ha-generic-picker",!0)],N.prototype,"genericPicker",void 0),N=(0,c.__decorate)([(0,h.EM)("ha-language-picker")],N),i()}catch(P){i(P)}}))},88422:function(e,t,a){a.a(e,(async function(e,t){try{var i=a(44734),o=a(56038),n=a(69683),r=a(6454),l=(a(28706),a(2892),a(62826)),s=a(52630),u=a(96196),c=a(77845),d=e([s]);s=(d.then?(await d)():d)[0];var h,v=e=>e,p=function(e){function t(){var e;(0,i.A)(this,t);for(var a=arguments.length,o=new Array(a),r=0;r<a;r++)o[r]=arguments[r];return(e=(0,n.A)(this,t,[].concat(o))).showDelay=150,e.hideDelay=150,e}return(0,r.A)(t,e),(0,o.A)(t,null,[{key:"styles",get:function(){return[s.A.styles,(0,u.AH)(h||(h=v`
        :host {
          --wa-tooltip-background-color: var(--secondary-background-color);
          --wa-tooltip-content-color: var(--primary-text-color);
          --wa-tooltip-font-family: var(
            --ha-tooltip-font-family,
            var(--ha-font-family-body)
          );
          --wa-tooltip-font-size: var(
            --ha-tooltip-font-size,
            var(--ha-font-size-s)
          );
          --wa-tooltip-font-weight: var(
            --ha-tooltip-font-weight,
            var(--ha-font-weight-normal)
          );
          --wa-tooltip-line-height: var(
            --ha-tooltip-line-height,
            var(--ha-line-height-condensed)
          );
          --wa-tooltip-padding: 8px;
          --wa-tooltip-border-radius: var(
            --ha-tooltip-border-radius,
            var(--ha-border-radius-sm)
          );
          --wa-tooltip-arrow-size: var(--ha-tooltip-arrow-size, 8px);
          --wa-z-index-tooltip: var(--ha-tooltip-z-index, 1000);
        }
      `))]}}])}(s.A);(0,l.__decorate)([(0,c.MZ)({attribute:"show-delay",type:Number})],p.prototype,"showDelay",void 0),(0,l.__decorate)([(0,c.MZ)({attribute:"hide-delay",type:Number})],p.prototype,"hideDelay",void 0),p=(0,l.__decorate)([(0,c.EM)("ha-tooltip")],p),t()}catch(g){t(g)}}))},10054:function(e,t,a){var i,o,n,r,l=a(61397),s=a(50264),u=a(44734),c=a(56038),d=a(69683),h=a(6454),v=a(25460),p=(a(28706),a(50113),a(62062),a(18111),a(20116),a(61701),a(26099),a(62826)),g=a(96196),_=a(77845),y=a(92542),f=a(55124),b=a(40404),m=a(62146),k=(a(56565),a(69869),e=>e),w="__NONE_OPTION__",A=function(e){function t(){var e;(0,u.A)(this,t);for(var a=arguments.length,i=new Array(a),o=0;o<a;o++)i[o]=arguments[o];return(e=(0,d.A)(this,t,[].concat(i))).disabled=!1,e.required=!1,e._debouncedUpdateVoices=(0,b.s)((()=>e._updateVoices()),500),e}return(0,h.A)(t,e),(0,c.A)(t,[{key:"render",value:function(){var e,t;if(!this._voices)return g.s6;var a=null!==(e=this.value)&&void 0!==e?e:this.required?null===(t=this._voices[0])||void 0===t?void 0:t.voice_id:w;return(0,g.qy)(i||(i=k`
      <ha-select
        .label=${0}
        .value=${0}
        .required=${0}
        .disabled=${0}
        @selected=${0}
        @closed=${0}
        fixedMenuPosition
        naturalMenuWidth
      >
        ${0}
        ${0}
      </ha-select>
    `),this.label||this.hass.localize("ui.components.tts-voice-picker.voice"),a,this.required,this.disabled,this._changed,f.d,this.required?g.s6:(0,g.qy)(o||(o=k`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),w,this.hass.localize("ui.components.tts-voice-picker.none")),this._voices.map((e=>(0,g.qy)(n||(n=k`<ha-list-item .value=${0}>
              ${0}
            </ha-list-item>`),e.voice_id,e.name))))}},{key:"willUpdate",value:function(e){(0,v.A)(t,"willUpdate",this,3)([e]),this.hasUpdated?(e.has("language")||e.has("engineId"))&&this._debouncedUpdateVoices():this._updateVoices()}},{key:"_updateVoices",value:(a=(0,s.A)((0,l.A)().m((function e(){return(0,l.A)().w((function(e){for(;;)switch(e.n){case 0:if(this.engineId&&this.language){e.n=1;break}return this._voices=void 0,e.a(2);case 1:return e.n=2,(0,m.z3)(this.hass,this.engineId,this.language);case 2:if(this._voices=e.v.voices,this.value){e.n=3;break}return e.a(2);case 3:this._voices&&this._voices.find((e=>e.voice_id===this.value))||(this.value=void 0,(0,y.r)(this,"value-changed",{value:this.value}));case 4:return e.a(2)}}),e,this)}))),function(){return a.apply(this,arguments)})},{key:"updated",value:function(e){var a,i,o;((0,v.A)(t,"updated",this,3)([e]),e.has("_voices")&&(null===(a=this._select)||void 0===a?void 0:a.value)!==this.value)&&(null===(i=this._select)||void 0===i||i.layoutOptions(),(0,y.r)(this,"value-changed",{value:null===(o=this._select)||void 0===o?void 0:o.value}))}},{key:"_changed",value:function(e){var t=e.target;!this.hass||""===t.value||t.value===this.value||void 0===this.value&&t.value===w||(this.value=t.value===w?void 0:t.value,(0,y.r)(this,"value-changed",{value:this.value}))}}]);var a}(g.WF);A.styles=(0,g.AH)(r||(r=k`
    ha-select {
      width: 100%;
    }
  `)),(0,p.__decorate)([(0,_.MZ)()],A.prototype,"value",void 0),(0,p.__decorate)([(0,_.MZ)()],A.prototype,"label",void 0),(0,p.__decorate)([(0,_.MZ)({attribute:!1})],A.prototype,"engineId",void 0),(0,p.__decorate)([(0,_.MZ)()],A.prototype,"language",void 0),(0,p.__decorate)([(0,_.MZ)({attribute:!1})],A.prototype,"hass",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean,reflect:!0})],A.prototype,"disabled",void 0),(0,p.__decorate)([(0,_.MZ)({type:Boolean})],A.prototype,"required",void 0),(0,p.__decorate)([(0,_.wk)()],A.prototype,"_voices",void 0),(0,p.__decorate)([(0,_.P)("ha-select")],A.prototype,"_select",void 0),A=(0,p.__decorate)([(0,_.EM)("ha-tts-voice-picker")],A)},71750:function(e,t,a){a.d(t,{eN:function(){return s},p7:function(){return n},q3:function(){return l},vO:function(){return r}});var i=a(20054),o=["hass"],n=e=>{var t=e.hass,a=(0,i.A)(e,o);return t.callApi("POST","cloud/login",a)},r=(e,t,a)=>e.callApi("POST","cloud/register",{email:t,password:a}),l=(e,t)=>e.callApi("POST","cloud/resend_confirm",{email:t}),s=e=>e.callWS({type:"cloud/status"})},62146:function(e,t,a){a.d(t,{EF:function(){return r},S_:function(){return i},Xv:function(){return l},ni:function(){return n},u1:function(){return s},z3:function(){return u}});var i=(e,t)=>e.callApi("POST","tts_get_url",t),o="media-source://tts/",n=e=>e.startsWith(o),r=e=>e.substring(19),l=(e,t,a)=>e.callWS({type:"tts/engine/list",language:t,country:a}),s=(e,t)=>e.callWS({type:"tts/engine/get",engine_id:t}),u=(e,t,a)=>e.callWS({type:"tts/engine/voices",engine_id:t,language:a})},4848:function(e,t,a){a.d(t,{P:function(){return o}});var i=a(92542),o=(e,t)=>(0,i.r)(e,"hass-notification",t)}}]);
//# sourceMappingURL=1283.5a805ca1dc76e2cb.js.map