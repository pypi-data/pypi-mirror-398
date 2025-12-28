"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["8350"],{68006:function(e,t,i){i.d(t,{z:function(){return a}});i(2892),i(26099),i(38781);var a=e=>{if(void 0!==e){if("object"!=typeof e){if("string"==typeof e||isNaN(e)){var t=(null==e?void 0:e.toString().split(":"))||[];if(1===t.length)return{seconds:Number(t[0])};if(t.length>3)return;var i=Number(t[2])||0,a=Math.floor(i);return{hours:Number(t[0])||0,minutes:Number(t[1])||0,seconds:a,milliseconds:Math.floor(1e3*Number((i-a).toFixed(4)))}}return{seconds:e}}if(!("days"in e))return e;var o=e.days,r=e.minutes,s=e.seconds,n=e.milliseconds,l=e.hours||0;return{hours:l=(l||0)+24*(o||0),minutes:r,seconds:s,milliseconds:n}}}},29261:function(e,t,i){var a,o,r,s,n,l,d,u,h,c=i(44734),p=i(56038),m=i(69683),v=i(6454),y=(i(28706),i(2892),i(26099),i(38781),i(68156),i(62826)),b=i(96196),f=i(77845),_=i(32288),g=i(92542),$=i(55124),x=(i(60733),i(56768),i(56565),i(69869),i(78740),e=>e),M=function(e){function t(){var e;(0,c.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,m.A)(this,t,[].concat(a))).autoValidate=!1,e.required=!1,e.format=12,e.disabled=!1,e.days=0,e.hours=0,e.minutes=0,e.seconds=0,e.milliseconds=0,e.dayLabel="",e.hourLabel="",e.minLabel="",e.secLabel="",e.millisecLabel="",e.enableSecond=!1,e.enableMillisecond=!1,e.enableDay=!1,e.noHoursLimit=!1,e.amPm="AM",e}return(0,v.A)(t,e),(0,p.A)(t,[{key:"render",value:function(){return(0,b.qy)(a||(a=x`
      ${0}
      <div class="time-input-wrap-wrap">
        <div class="time-input-wrap">
          ${0}

          <ha-textfield
            id="hour"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            name="hours"
            @change=${0}
            @focusin=${0}
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max=${0}
            min="0"
            .disabled=${0}
            suffix=":"
            class="hasSuffix"
          >
          </ha-textfield>
          <ha-textfield
            id="min"
            type="number"
            inputmode="numeric"
            .value=${0}
            .label=${0}
            @change=${0}
            @focusin=${0}
            name="minutes"
            no-spinner
            .required=${0}
            .autoValidate=${0}
            maxlength="2"
            max="59"
            min="0"
            .disabled=${0}
            .suffix=${0}
            class=${0}
          >
          </ha-textfield>
          ${0}
          ${0}
          ${0}
        </div>

        ${0}
      </div>
      ${0}
    `),this.label?(0,b.qy)(o||(o=x`<label>${0}${0}</label>`),this.label,this.required?" *":""):b.s6,this.enableDay?(0,b.qy)(r||(r=x`
                <ha-textfield
                  id="day"
                  type="number"
                  inputmode="numeric"
                  .value=${0}
                  .label=${0}
                  name="days"
                  @change=${0}
                  @focusin=${0}
                  no-spinner
                  .required=${0}
                  .autoValidate=${0}
                  min="0"
                  .disabled=${0}
                  suffix=":"
                  class="hasSuffix"
                >
                </ha-textfield>
              `),this.days.toFixed(),this.dayLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):b.s6,this.hours.toFixed(),this.hourLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,(0,_.J)(this._hourMax),this.disabled,this._formatValue(this.minutes),this.minLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableSecond?":":"",this.enableSecond?"has-suffix":"",this.enableSecond?(0,b.qy)(s||(s=x`<ha-textfield
                id="sec"
                type="number"
                inputmode="numeric"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="seconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="2"
                max="59"
                min="0"
                .disabled=${0}
                .suffix=${0}
                class=${0}
              >
              </ha-textfield>`),this._formatValue(this.seconds),this.secLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableMillisecond?":":"",this.enableMillisecond?"has-suffix":""):b.s6,this.enableMillisecond?(0,b.qy)(n||(n=x`<ha-textfield
                id="millisec"
                type="number"
                .value=${0}
                .label=${0}
                @change=${0}
                @focusin=${0}
                name="milliseconds"
                no-spinner
                .required=${0}
                .autoValidate=${0}
                maxlength="3"
                max="999"
                min="0"
                .disabled=${0}
              >
              </ha-textfield>`),this._formatValue(this.milliseconds,3),this.millisecLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):b.s6,!this.clearable||this.required||this.disabled?b.s6:(0,b.qy)(l||(l=x`<ha-icon-button
                label="clear"
                @click=${0}
                .path=${0}
              ></ha-icon-button>`),this._clearValue,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"),24===this.format?b.s6:(0,b.qy)(d||(d=x`<ha-select
              .required=${0}
              .value=${0}
              .disabled=${0}
              name="amPm"
              naturalMenuWidth
              fixedMenuPosition
              @selected=${0}
              @closed=${0}
            >
              <ha-list-item value="AM">AM</ha-list-item>
              <ha-list-item value="PM">PM</ha-list-item>
            </ha-select>`),this.required,this.amPm,this.disabled,this._valueChanged,$.d),this.helper?(0,b.qy)(u||(u=x`<ha-input-helper-text .disabled=${0}
            >${0}</ha-input-helper-text
          >`),this.disabled,this.helper):b.s6)}},{key:"_clearValue",value:function(){(0,g.r)(this,"value-changed")}},{key:"_valueChanged",value:function(e){var t=e.currentTarget;this[t.name]="amPm"===t.name?t.value:Number(t.value);var i={hours:this.hours,minutes:this.minutes,seconds:this.seconds,milliseconds:this.milliseconds};this.enableDay&&(i.days=this.days),12===this.format&&(i.amPm=this.amPm),(0,g.r)(this,"value-changed",{value:i})}},{key:"_onFocus",value:function(e){e.currentTarget.select()}},{key:"_formatValue",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;return e.toString().padStart(t,"0")}},{key:"_hourMax",get:function(){if(!this.noHoursLimit)return 12===this.format?12:23}}])}(b.WF);M.styles=(0,b.AH)(h||(h=x`
    :host([clearable]) {
      position: relative;
    }
    .time-input-wrap-wrap {
      display: flex;
    }
    .time-input-wrap {
      display: flex;
      flex: var(--time-input-flex, unset);
      border-radius: var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--mdc-shape-small, var(--ha-border-radius-sm))
        var(--ha-border-radius-square) var(--ha-border-radius-square);
      overflow: hidden;
      position: relative;
      direction: ltr;
      padding-right: 3px;
    }
    ha-textfield {
      width: 60px;
      flex-grow: 1;
      text-align: center;
      --mdc-shape-small: 0;
      --text-field-appearance: none;
      --text-field-padding: 0 4px;
      --text-field-suffix-padding-left: 2px;
      --text-field-suffix-padding-right: 0;
      --text-field-text-align: center;
    }
    ha-textfield.hasSuffix {
      --text-field-padding: 0 0 0 4px;
    }
    ha-textfield:first-child {
      --text-field-border-top-left-radius: var(--mdc-shape-medium);
    }
    ha-textfield:last-child {
      --text-field-border-top-right-radius: var(--mdc-shape-medium);
    }
    ha-select {
      --mdc-shape-small: 0;
      width: 85px;
    }
    :host([clearable]) .mdc-select__anchor {
      padding-inline-end: var(--select-selected-text-padding-end, 12px);
    }
    ha-icon-button {
      position: relative;
      --mdc-icon-button-size: 36px;
      --mdc-icon-size: 20px;
      color: var(--secondary-text-color);
      direction: var(--direction);
      display: flex;
      align-items: center;
      background-color: var(--mdc-text-field-fill-color, whitesmoke);
      border-bottom-style: solid;
      border-bottom-width: 1px;
    }
    label {
      -moz-osx-font-smoothing: var(--ha-moz-osx-font-smoothing);
      -webkit-font-smoothing: var(--ha-font-smoothing);
      font-family: var(
        --mdc-typography-body2-font-family,
        var(--mdc-typography-font-family, var(--ha-font-family-body))
      );
      font-size: var(--mdc-typography-body2-font-size, var(--ha-font-size-s));
      line-height: var(
        --mdc-typography-body2-line-height,
        var(--ha-line-height-condensed)
      );
      font-weight: var(
        --mdc-typography-body2-font-weight,
        var(--ha-font-weight-normal)
      );
      letter-spacing: var(
        --mdc-typography-body2-letter-spacing,
        0.0178571429em
      );
      text-decoration: var(--mdc-typography-body2-text-decoration, inherit);
      text-transform: var(--mdc-typography-body2-text-transform, inherit);
      color: var(--mdc-theme-text-primary-on-background, rgba(0, 0, 0, 0.87));
      padding-left: 4px;
      padding-inline-start: 4px;
      padding-inline-end: initial;
    }
    ha-input-helper-text {
      padding-top: 8px;
      line-height: var(--ha-line-height-condensed);
    }
  `)),(0,y.__decorate)([(0,f.MZ)()],M.prototype,"label",void 0),(0,y.__decorate)([(0,f.MZ)()],M.prototype,"helper",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"auto-validate",type:Boolean})],M.prototype,"autoValidate",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"required",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"format",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"days",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"hours",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"minutes",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"seconds",void 0),(0,y.__decorate)([(0,f.MZ)({type:Number})],M.prototype,"milliseconds",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"day-label"})],M.prototype,"dayLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"hour-label"})],M.prototype,"hourLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"min-label"})],M.prototype,"minLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"sec-label"})],M.prototype,"secLabel",void 0),(0,y.__decorate)([(0,f.MZ)({type:String,attribute:"ms-label"})],M.prototype,"millisecLabel",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-second",type:Boolean})],M.prototype,"enableSecond",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-millisecond",type:Boolean})],M.prototype,"enableMillisecond",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"enable-day",type:Boolean})],M.prototype,"enableDay",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:"no-hours-limit",type:Boolean})],M.prototype,"noHoursLimit",void 0),(0,y.__decorate)([(0,f.MZ)({attribute:!1})],M.prototype,"amPm",void 0),(0,y.__decorate)([(0,f.MZ)({type:Boolean,reflect:!0})],M.prototype,"clearable",void 0),M=(0,y.__decorate)([(0,f.EM)("ha-base-time-input")],M)},33464:function(e,t,i){var a,o=i(44734),r=i(56038),s=i(69683),n=i(6454),l=(i(28706),i(2892),i(62826)),d=i(96196),u=i(77845),h=i(92542),c=(i(29261),e=>e),p=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).required=!1,e.enableMillisecond=!1,e.enableDay=!1,e.disabled=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,d.qy)(a||(a=c`
      <ha-base-time-input
        .label=${0}
        .helper=${0}
        .required=${0}
        .clearable=${0}
        .autoValidate=${0}
        .disabled=${0}
        errorMessage="Required"
        enable-second
        .enableMillisecond=${0}
        .enableDay=${0}
        format="24"
        .days=${0}
        .hours=${0}
        .minutes=${0}
        .seconds=${0}
        .milliseconds=${0}
        @value-changed=${0}
        no-hours-limit
        day-label="dd"
        hour-label="hh"
        min-label="mm"
        sec-label="ss"
        ms-label="ms"
      ></ha-base-time-input>
    `),this.label,this.helper,this.required,!this.required&&void 0!==this.data,this.required,this.disabled,this.enableMillisecond,this.enableDay,this._days,this._hours,this._minutes,this._seconds,this._milliseconds,this._durationChanged)}},{key:"_days",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.days?Number(this.data.days):this.required||this.data?0:NaN}},{key:"_hours",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.hours?Number(this.data.hours):this.required||this.data?0:NaN}},{key:"_minutes",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.minutes?Number(this.data.minutes):this.required||this.data?0:NaN}},{key:"_seconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.seconds?Number(this.data.seconds):this.required||this.data?0:NaN}},{key:"_milliseconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.milliseconds?Number(this.data.milliseconds):this.required||this.data?0:NaN}},{key:"_durationChanged",value:function(e){e.stopPropagation();var t,i=e.detail.value?Object.assign({},e.detail.value):void 0;i&&(i.hours||(i.hours=0),i.minutes||(i.minutes=0),i.seconds||(i.seconds=0),"days"in i&&(i.days||(i.days=0)),"milliseconds"in i&&(i.milliseconds||(i.milliseconds=0)),this.enableMillisecond||i.milliseconds?i.milliseconds>999&&(i.seconds+=Math.floor(i.milliseconds/1e3),i.milliseconds%=1e3):delete i.milliseconds,i.seconds>59&&(i.minutes+=Math.floor(i.seconds/60),i.seconds%=60),i.minutes>59&&(i.hours+=Math.floor(i.minutes/60),i.minutes%=60),this.enableDay&&i.hours>24&&(i.days=(null!==(t=i.days)&&void 0!==t?t:0)+Math.floor(i.hours/24),i.hours%=24));(0,h.r)(this,"value-changed",{value:i})}}])}(d.WF);(0,l.__decorate)([(0,u.MZ)({attribute:!1})],p.prototype,"data",void 0),(0,l.__decorate)([(0,u.MZ)()],p.prototype,"label",void 0),(0,l.__decorate)([(0,u.MZ)()],p.prototype,"helper",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],p.prototype,"required",void 0),(0,l.__decorate)([(0,u.MZ)({attribute:"enable-millisecond",type:Boolean})],p.prototype,"enableMillisecond",void 0),(0,l.__decorate)([(0,u.MZ)({attribute:"enable-day",type:Boolean})],p.prototype,"enableDay",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,u.EM)("ha-duration-input")],p)},88867:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t),i.d(t,{HaIconPicker:function(){return V}});var o=i(31432),r=i(44734),s=i(56038),n=i(69683),l=i(6454),d=i(61397),u=i(94741),h=i(50264),c=(i(28706),i(2008),i(74423),i(23792),i(62062),i(44114),i(34782),i(26910),i(18111),i(22489),i(7588),i(61701),i(13579),i(26099),i(3362),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(23500),i(62953),i(62826)),p=i(96196),m=i(77845),v=i(22786),y=i(92542),b=i(33978),f=i(55179),_=(i(22598),i(94343),e([f]));f=(_.then?(await _)():_)[0];var g,$,x,M,k,q=e=>e,w=[],Z=!1,A=function(){var e=(0,h.A)((0,d.A)().m((function e(){var t,a;return(0,d.A)().w((function(e){for(;;)switch(e.n){case 0:return Z=!0,e.n=1,i.e("3451").then(i.t.bind(i,83174,19));case 1:return t=e.v,w=t.default.map((e=>({icon:`mdi:${e.name}`,parts:new Set(e.name.split("-")),keywords:e.keywords}))),a=[],Object.keys(b.y).forEach((e=>{a.push(L(e))})),e.n=2,Promise.all(a);case 2:e.v.forEach((e=>{var t;(t=w).push.apply(t,(0,u.A)(e))}));case 3:return e.a(2)}}),e)})));return function(){return e.apply(this,arguments)}}(),L=function(){var e=(0,h.A)((0,d.A)().m((function e(t){var i,a,o;return(0,d.A)().w((function(e){for(;;)switch(e.p=e.n){case 0:if(e.p=0,"function"==typeof(i=b.y[t].getIconList)){e.n=1;break}return e.a(2,[]);case 1:return e.n=2,i();case 2:return a=e.v,o=a.map((e=>{var i;return{icon:`${t}:${e.name}`,parts:new Set(e.name.split("-")),keywords:null!==(i=e.keywords)&&void 0!==i?i:[]}})),e.a(2,o);case 3:return e.p=3,e.v,console.warn(`Unable to load icon list for ${t} iconset`),e.a(2,[])}}),e,null,[[0,3]])})));return function(t){return e.apply(this,arguments)}}(),N=e=>(0,p.qy)(g||(g=q`
  <ha-combo-box-item type="button">
    <ha-icon .icon=${0} slot="start"></ha-icon>
    ${0}
  </ha-combo-box-item>
`),e.icon,e.icon),V=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(a))).disabled=!1,e.required=!1,e.invalid=!1,e._filterIcons=(0,v.A)((function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:w;if(!e)return t;var i,a=[],r=(e,t)=>a.push({icon:e,rank:t}),s=(0,o.A)(t);try{for(s.s();!(i=s.n()).done;){var n=i.value;n.parts.has(e)?r(n.icon,1):n.keywords.includes(e)?r(n.icon,2):n.icon.includes(e)?r(n.icon,3):n.keywords.some((t=>t.includes(e)))&&r(n.icon,4)}}catch(l){s.e(l)}finally{s.f()}return 0===a.length&&r(e,0),a.sort(((e,t)=>e.rank-t.rank))})),e._iconProvider=(t,i)=>{var a=e._filterIcons(t.filter.toLowerCase(),w),o=t.page*t.pageSize,r=o+t.pageSize;i(a.slice(o,r),a.length)},e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){return(0,p.qy)($||($=q`
      <ha-combo-box
        .hass=${0}
        item-value-path="icon"
        item-label-path="icon"
        .value=${0}
        allow-custom-value
        .dataProvider=${0}
        .label=${0}
        .helper=${0}
        .disabled=${0}
        .required=${0}
        .placeholder=${0}
        .errorMessage=${0}
        .invalid=${0}
        .renderer=${0}
        icon
        @opened-changed=${0}
        @value-changed=${0}
      >
        ${0}
      </ha-combo-box>
    `),this.hass,this._value,Z?this._iconProvider:void 0,this.label,this.helper,this.disabled,this.required,this.placeholder,this.errorMessage,this.invalid,N,this._openedChanged,this._valueChanged,this._value||this.placeholder?(0,p.qy)(x||(x=q`
              <ha-icon .icon=${0} slot="icon">
              </ha-icon>
            `),this._value||this.placeholder):(0,p.qy)(M||(M=q`<slot slot="icon" name="fallback"></slot>`)))}},{key:"_openedChanged",value:(i=(0,h.A)((0,d.A)().m((function e(t){return(0,d.A)().w((function(e){for(;;)switch(e.n){case 0:if(!t.detail.value||Z){e.n=2;break}return e.n=1,A();case 1:this.requestUpdate();case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_valueChanged",value:function(e){e.stopPropagation(),this._setValue(e.detail.value)}},{key:"_setValue",value:function(e){this.value=e,(0,y.r)(this,"value-changed",{value:this._value},{bubbles:!1,composed:!1})}},{key:"_value",get:function(){return this.value||""}}]);var i}(p.WF);V.styles=(0,p.AH)(k||(k=q`
    *[slot="icon"] {
      color: var(--primary-text-color);
      position: relative;
      bottom: 2px;
    }
    *[slot="prefix"] {
      margin-right: 8px;
      margin-inline-end: 8px;
      margin-inline-start: initial;
    }
  `)),(0,c.__decorate)([(0,m.MZ)({attribute:!1})],V.prototype,"hass",void 0),(0,c.__decorate)([(0,m.MZ)()],V.prototype,"value",void 0),(0,c.__decorate)([(0,m.MZ)()],V.prototype,"label",void 0),(0,c.__decorate)([(0,m.MZ)()],V.prototype,"helper",void 0),(0,c.__decorate)([(0,m.MZ)()],V.prototype,"placeholder",void 0),(0,c.__decorate)([(0,m.MZ)({attribute:"error-message"})],V.prototype,"errorMessage",void 0),(0,c.__decorate)([(0,m.MZ)({type:Boolean})],V.prototype,"disabled",void 0),(0,c.__decorate)([(0,m.MZ)({type:Boolean})],V.prototype,"required",void 0),(0,c.__decorate)([(0,m.MZ)({type:Boolean})],V.prototype,"invalid",void 0),V=(0,c.__decorate)([(0,m.EM)("ha-icon-picker")],V),a()}catch(C){a(C)}}))},55421:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t);var o=i(44734),r=i(56038),s=i(69683),n=i(6454),l=(i(28706),i(62826)),d=i(96196),u=i(77845),h=i(68006),c=i(92542),p=(i(70524),i(33464),i(48543),i(88867)),m=(i(78740),i(39396)),v=e([p]);p=(v.then?(await v)():v)[0];var y,b,f=e=>e,_=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),r=0;r<i;r++)a[r]=arguments[r];return(e=(0,s.A)(this,t,[].concat(a))).new=!1,e.disabled=!1,e}return(0,n.A)(t,e),(0,r.A)(t,[{key:"item",set:function(e){this._item=e,e?(this._name=e.name||"",this._icon=e.icon||"",this._duration=e.duration||"00:00:00",this._restore=e.restore||!1):(this._name="",this._icon="",this._duration="00:00:00",this._restore=!1),this._setDurationData()}},{key:"focus",value:function(){this.updateComplete.then((()=>{var e;return null===(e=this.shadowRoot)||void 0===e||null===(e=e.querySelector("[dialogInitialFocus]"))||void 0===e?void 0:e.focus()}))}},{key:"render",value:function(){return this.hass?(0,d.qy)(y||(y=f`
      <div class="form">
        <ha-textfield
          .value=${0}
          .configValue=${0}
          @input=${0}
          .label=${0}
          autoValidate
          required
          .validationMessage=${0}
          dialogInitialFocus
          .disabled=${0}
        ></ha-textfield>
        <ha-icon-picker
          .hass=${0}
          .value=${0}
          .configValue=${0}
          @value-changed=${0}
          .label=${0}
          .disabled=${0}
        ></ha-icon-picker>
        <ha-duration-input
          .configValue=${0}
          .data=${0}
          @value-changed=${0}
          .disabled=${0}
        ></ha-duration-input>
        <ha-formfield
          .label=${0}
        >
          <ha-checkbox
            .configValue=${0}
            .checked=${0}
            @click=${0}
            .disabled=${0}
          >
          </ha-checkbox>
        </ha-formfield>
      </div>
    `),this._name,"name",this._valueChanged,this.hass.localize("ui.dialogs.helper_settings.generic.name"),this.hass.localize("ui.dialogs.helper_settings.required_error_msg"),this.disabled,this.hass,this._icon,"icon",this._valueChanged,this.hass.localize("ui.dialogs.helper_settings.generic.icon"),this.disabled,"duration",this._duration_data,this._valueChanged,this.disabled,this.hass.localize("ui.dialogs.helper_settings.timer.restore"),"restore",this._restore,this._toggleRestore,this.disabled):d.s6}},{key:"_valueChanged",value:function(e){var t;if(this.new||this._item){e.stopPropagation();var i=e.target.configValue,a=(null===(t=e.detail)||void 0===t?void 0:t.value)||e.target.value;if(this[`_${i}`]!==a){var o=Object.assign({},this._item);a?o[i]=a:delete o[i],(0,c.r)(this,"value-changed",{value:o})}}}},{key:"_toggleRestore",value:function(){this.disabled||(this._restore=!this._restore,(0,c.r)(this,"value-changed",{value:Object.assign(Object.assign({},this._item),{},{restore:this._restore})}))}},{key:"_setDurationData",value:function(){var e;if("object"==typeof this._duration&&null!==this._duration){var t=this._duration;e={hours:"string"==typeof t.hours?parseFloat(t.hours):t.hours,minutes:"string"==typeof t.minutes?parseFloat(t.minutes):t.minutes,seconds:"string"==typeof t.seconds?parseFloat(t.seconds):t.seconds}}else e=this._duration;this._duration_data=(0,h.z)(e)}}],[{key:"styles",get:function(){return[m.RF,(0,d.AH)(b||(b=f`
        .form {
          color: var(--primary-text-color);
        }
        ha-textfield,
        ha-duration-input {
          display: block;
          margin: 8px 0;
        }
      `))]}}])}(d.WF);(0,l.__decorate)([(0,u.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"new",void 0),(0,l.__decorate)([(0,u.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,l.__decorate)([(0,u.wk)()],_.prototype,"_name",void 0),(0,l.__decorate)([(0,u.wk)()],_.prototype,"_icon",void 0),(0,l.__decorate)([(0,u.wk)()],_.prototype,"_duration",void 0),(0,l.__decorate)([(0,u.wk)()],_.prototype,"_duration_data",void 0),(0,l.__decorate)([(0,u.wk)()],_.prototype,"_restore",void 0),_=(0,l.__decorate)([(0,u.EM)("ha-timer-form")],_),a()}catch(g){a(g)}}))}}]);
//# sourceMappingURL=8350.d6d5bd4d2548fd87.js.map