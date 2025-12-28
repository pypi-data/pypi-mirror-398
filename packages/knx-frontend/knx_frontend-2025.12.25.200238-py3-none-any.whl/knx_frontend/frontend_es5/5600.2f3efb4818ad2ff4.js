"use strict";(self.webpackChunkknx_frontend=self.webpackChunkknx_frontend||[]).push([["5600"],{62100:function(e,t,i){var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=i(62826),l=i(77845),c=i(74687),d=function(e){function t(){return(0,a.A)(this,t),(0,n.A)(this,t,[c.PV,c.am,e=>({device_id:e||"",domain:"",entity_id:""})])}return(0,s.A)(t,e),(0,o.A)(t,[{key:"NO_AUTOMATION_TEXT",get:function(){return this.hass.localize("ui.panel.config.devices.automation.actions.no_actions")}},{key:"UNKNOWN_AUTOMATION_TEXT",get:function(){return this.hass.localize("ui.panel.config.devices.automation.actions.unknown_action")}}])}(i(7078).V);d=(0,r.__decorate)([(0,l.EM)("ha-device-action-picker")],d)},29261:function(e,t,i){var a,o,n,s,r,l,c,d,h,u=i(44734),p=i(56038),v=i(69683),_=i(6454),y=(i(28706),i(2892),i(26099),i(38781),i(68156),i(62826)),f=i(96196),m=i(77845),g=i(32288),b=i(92542),$=i(55124),A=(i(60733),i(56768),i(56565),i(69869),i(78740),e=>e),w=function(e){function t(){var e;(0,u.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,v.A)(this,t,[].concat(a))).autoValidate=!1,e.required=!1,e.format=12,e.disabled=!1,e.days=0,e.hours=0,e.minutes=0,e.seconds=0,e.milliseconds=0,e.dayLabel="",e.hourLabel="",e.minLabel="",e.secLabel="",e.millisecLabel="",e.enableSecond=!1,e.enableMillisecond=!1,e.enableDay=!1,e.noHoursLimit=!1,e.amPm="AM",e}return(0,_.A)(t,e),(0,p.A)(t,[{key:"render",value:function(){return(0,f.qy)(a||(a=A`
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
    `),this.label?(0,f.qy)(o||(o=A`<label>${0}${0}</label>`),this.label,this.required?" *":""):f.s6,this.enableDay?(0,f.qy)(n||(n=A`
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
              `),this.days.toFixed(),this.dayLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):f.s6,this.hours.toFixed(),this.hourLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,(0,g.J)(this._hourMax),this.disabled,this._formatValue(this.minutes),this.minLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableSecond?":":"",this.enableSecond?"has-suffix":"",this.enableSecond?(0,f.qy)(s||(s=A`<ha-textfield
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
              </ha-textfield>`),this._formatValue(this.seconds),this.secLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled,this.enableMillisecond?":":"",this.enableMillisecond?"has-suffix":""):f.s6,this.enableMillisecond?(0,f.qy)(r||(r=A`<ha-textfield
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
              </ha-textfield>`),this._formatValue(this.milliseconds,3),this.millisecLabel,this._valueChanged,this._onFocus,this.required,this.autoValidate,this.disabled):f.s6,!this.clearable||this.required||this.disabled?f.s6:(0,f.qy)(l||(l=A`<ha-icon-button
                label="clear"
                @click=${0}
                .path=${0}
              ></ha-icon-button>`),this._clearValue,"M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z"),24===this.format?f.s6:(0,f.qy)(c||(c=A`<ha-select
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
            </ha-select>`),this.required,this.amPm,this.disabled,this._valueChanged,$.d),this.helper?(0,f.qy)(d||(d=A`<ha-input-helper-text .disabled=${0}
            >${0}</ha-input-helper-text
          >`),this.disabled,this.helper):f.s6)}},{key:"_clearValue",value:function(){(0,b.r)(this,"value-changed")}},{key:"_valueChanged",value:function(e){var t=e.currentTarget;this[t.name]="amPm"===t.name?t.value:Number(t.value);var i={hours:this.hours,minutes:this.minutes,seconds:this.seconds,milliseconds:this.milliseconds};this.enableDay&&(i.days=this.days),12===this.format&&(i.amPm=this.amPm),(0,b.r)(this,"value-changed",{value:i})}},{key:"_onFocus",value:function(e){e.currentTarget.select()}},{key:"_formatValue",value:function(e){var t=arguments.length>1&&void 0!==arguments[1]?arguments[1]:2;return e.toString().padStart(t,"0")}},{key:"_hourMax",get:function(){if(!this.noHoursLimit)return 12===this.format?12:23}}])}(f.WF);w.styles=(0,f.AH)(h||(h=A`
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
  `)),(0,y.__decorate)([(0,m.MZ)()],w.prototype,"label",void 0),(0,y.__decorate)([(0,m.MZ)()],w.prototype,"helper",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:"auto-validate",type:Boolean})],w.prototype,"autoValidate",void 0),(0,y.__decorate)([(0,m.MZ)({type:Boolean})],w.prototype,"required",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"format",void 0),(0,y.__decorate)([(0,m.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"days",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"hours",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"minutes",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"seconds",void 0),(0,y.__decorate)([(0,m.MZ)({type:Number})],w.prototype,"milliseconds",void 0),(0,y.__decorate)([(0,m.MZ)({type:String,attribute:"day-label"})],w.prototype,"dayLabel",void 0),(0,y.__decorate)([(0,m.MZ)({type:String,attribute:"hour-label"})],w.prototype,"hourLabel",void 0),(0,y.__decorate)([(0,m.MZ)({type:String,attribute:"min-label"})],w.prototype,"minLabel",void 0),(0,y.__decorate)([(0,m.MZ)({type:String,attribute:"sec-label"})],w.prototype,"secLabel",void 0),(0,y.__decorate)([(0,m.MZ)({type:String,attribute:"ms-label"})],w.prototype,"millisecLabel",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:"enable-second",type:Boolean})],w.prototype,"enableSecond",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:"enable-millisecond",type:Boolean})],w.prototype,"enableMillisecond",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:"enable-day",type:Boolean})],w.prototype,"enableDay",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:"no-hours-limit",type:Boolean})],w.prototype,"noHoursLimit",void 0),(0,y.__decorate)([(0,m.MZ)({attribute:!1})],w.prototype,"amPm",void 0),(0,y.__decorate)([(0,m.MZ)({type:Boolean,reflect:!0})],w.prototype,"clearable",void 0),w=(0,y.__decorate)([(0,m.EM)("ha-base-time-input")],w)},33464:function(e,t,i){var a,o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(28706),i(2892),i(62826)),c=i(96196),d=i(77845),h=i(92542),u=(i(29261),e=>e),p=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).required=!1,e.enableMillisecond=!1,e.enableDay=!1,e.disabled=!1,e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,c.qy)(a||(a=u`
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
    `),this.label,this.helper,this.required,!this.required&&void 0!==this.data,this.required,this.disabled,this.enableMillisecond,this.enableDay,this._days,this._hours,this._minutes,this._seconds,this._milliseconds,this._durationChanged)}},{key:"_days",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.days?Number(this.data.days):this.required||this.data?0:NaN}},{key:"_hours",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.hours?Number(this.data.hours):this.required||this.data?0:NaN}},{key:"_minutes",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.minutes?Number(this.data.minutes):this.required||this.data?0:NaN}},{key:"_seconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.seconds?Number(this.data.seconds):this.required||this.data?0:NaN}},{key:"_milliseconds",get:function(){var e;return null!==(e=this.data)&&void 0!==e&&e.milliseconds?Number(this.data.milliseconds):this.required||this.data?0:NaN}},{key:"_durationChanged",value:function(e){e.stopPropagation();var t,i=e.detail.value?Object.assign({},e.detail.value):void 0;i&&(i.hours||(i.hours=0),i.minutes||(i.minutes=0),i.seconds||(i.seconds=0),"days"in i&&(i.days||(i.days=0)),"milliseconds"in i&&(i.milliseconds||(i.milliseconds=0)),this.enableMillisecond||i.milliseconds?i.milliseconds>999&&(i.seconds+=Math.floor(i.milliseconds/1e3),i.milliseconds%=1e3):delete i.milliseconds,i.seconds>59&&(i.minutes+=Math.floor(i.seconds/60),i.seconds%=60),i.minutes>59&&(i.hours+=Math.floor(i.minutes/60),i.minutes%=60),this.enableDay&&i.hours>24&&(i.days=(null!==(t=i.days)&&void 0!==t?t:0)+Math.floor(i.hours/24),i.hours%=24));(0,h.r)(this,"value-changed",{value:i})}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],p.prototype,"data",void 0),(0,l.__decorate)([(0,d.MZ)()],p.prototype,"label",void 0),(0,l.__decorate)([(0,d.MZ)()],p.prototype,"helper",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],p.prototype,"required",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:"enable-millisecond",type:Boolean})],p.prototype,"enableMillisecond",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:"enable-day",type:Boolean})],p.prototype,"enableDay",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,d.EM)("ha-duration-input")],p)},35219:function(e,t,i){i.a(e,(async function(e,a){try{i.r(t),i.d(t,{HaActionSelector:function(){return w}});var o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(28706),i(62826)),c=i(16527),d=i(96196),h=i(77845),u=i(22786),p=i(34972),v=i(22800),_=i(29272),y=i(10085),f=i(10754),m=e([f]);f=(m.then?(await m)():m)[0];var g,b,$,A=e=>e,w=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).narrow=!1,e.disabled=!1,e.hassSubscribeRequiredHostProps=["_entitiesContext"],e._actions=(0,u.A)((e=>e?(0,_.Rn)(e):[])),e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"firstUpdated",value:function(){this._entityReg||(this._entitiesContext=new c.DT(this,{context:p.ih,initialValue:[]}))}},{key:"hassSubscribe",value:function(){return[(0,v.Bz)(this.hass.connection,(e=>{this._entitiesContext.setValue(e)}))]}},{key:"expandAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.expandAll()}},{key:"collapseAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.collapseAll()}},{key:"render",value:function(){var e;return(0,d.qy)(g||(g=A`
      ${0}
      <ha-automation-action
        .disabled=${0}
        .actions=${0}
        .hass=${0}
        .narrow=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
    `),this.label?(0,d.qy)(b||(b=A`<label>${0}</label>`),this.label):d.s6,this.disabled,this._actions(this.value),this.hass,this.narrow,!(null===(e=this.selector.action)||void 0===e||!e.optionsInSidebar))}}])}((0,y.E)(d.WF));w.styles=(0,d.AH)($||($=A`
    ha-automation-action {
      display: block;
    }
    label {
      display: block;
      margin-bottom: 4px;
      font-weight: var(--ha-font-weight-medium);
      color: var(--secondary-text-color);
    }
  `)),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean})],w.prototype,"narrow",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"selector",void 0),(0,l.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"value",void 0),(0,l.__decorate)([(0,h.MZ)()],w.prototype,"label",void 0),(0,l.__decorate)([(0,h.MZ)({type:Boolean,reflect:!0})],w.prototype,"disabled",void 0),(0,l.__decorate)([(0,h.wk)(),(0,c.Fg)({context:p.ih,subscribe:!0})],w.prototype,"_entityReg",void 0),(0,l.__decorate)([(0,h.wk)()],w.prototype,"_entitiesContext",void 0),(0,l.__decorate)([(0,h.P)("ha-automation-action")],w.prototype,"_actionElement",void 0),w=(0,l.__decorate)([(0,h.EM)("ha-selector-action")],w),a()}catch(M){a(M)}}))},265:function(e,t,i){i.d(t,{EN:function(){return l},I8:function(){return h},L_:function(){return d},MC:function(){return c},O$:function(){return o},bM:function(){return r},ix:function(){return n},rP:function(){return s}});i(23792),i(26099),i(31415),i(17642),i(58004),i(33853),i(45876),i(32475),i(15024),i(31698),i(62953);var a="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z",o={condition:"M4 2A2 2 0 0 0 2 4V12H4V8H6V12H8V4A2 2 0 0 0 6 2H4M4 4H6V6H4M22 15.5V14A2 2 0 0 0 20 12H16V22H20A2 2 0 0 0 22 20V18.5A1.54 1.54 0 0 0 20.5 17A1.54 1.54 0 0 0 22 15.5M20 20H18V18H20V20M20 16H18V14H20M5.79 21.61L4.21 20.39L18.21 2.39L19.79 3.61Z",delay:"M12,20A7,7 0 0,1 5,13A7,7 0 0,1 12,6A7,7 0 0,1 19,13A7,7 0 0,1 12,20M19.03,7.39L20.45,5.97C20,5.46 19.55,5 19.04,4.56L17.62,6C16.07,4.74 14.12,4 12,4A9,9 0 0,0 3,13A9,9 0 0,0 12,22C17,22 21,17.97 21,13C21,10.88 20.26,8.93 19.03,7.39M11,14H13V8H11M15,1H9V3H15V1Z",event:"M10,9A1,1 0 0,1 11,8A1,1 0 0,1 12,9V13.47L13.21,13.6L18.15,15.79C18.68,16.03 19,16.56 19,17.14V21.5C18.97,22.32 18.32,22.97 17.5,23H11C10.62,23 10.26,22.85 10,22.57L5.1,18.37L5.84,17.6C6.03,17.39 6.3,17.28 6.58,17.28H6.8L10,19V9M11,5A4,4 0 0,1 15,9C15,10.5 14.2,11.77 13,12.46V11.24C13.61,10.69 14,9.89 14,9A3,3 0 0,0 11,6A3,3 0 0,0 8,9C8,9.89 8.39,10.69 9,11.24V12.46C7.8,11.77 7,10.5 7,9A4,4 0 0,1 11,5M11,3A6,6 0 0,1 17,9C17,10.7 16.29,12.23 15.16,13.33L14.16,12.88C15.28,11.96 16,10.56 16,9A5,5 0 0,0 11,4A5,5 0 0,0 6,9C6,11.05 7.23,12.81 9,13.58V14.66C6.67,13.83 5,11.61 5,9A6,6 0 0,1 11,3Z",play_media:"M8,5.14V19.14L19,12.14L8,5.14Z",service:"M12,5A2,2 0 0,1 14,7C14,7.24 13.96,7.47 13.88,7.69C17.95,8.5 21,11.91 21,16H3C3,11.91 6.05,8.5 10.12,7.69C10.04,7.47 10,7.24 10,7A2,2 0 0,1 12,5M22,19H2V17H22V19Z",wait_template:"M8,3A2,2 0 0,0 6,5V9A2,2 0 0,1 4,11H3V13H4A2,2 0 0,1 6,15V19A2,2 0 0,0 8,21H10V19H8V14A2,2 0 0,0 6,12A2,2 0 0,0 8,10V5H10V3M16,3A2,2 0 0,1 18,5V9A2,2 0 0,0 20,11H21V13H20A2,2 0 0,0 18,15V19A2,2 0 0,1 16,21H14V19H16V14A2,2 0 0,1 18,12A2,2 0 0,1 16,10V5H14V3H16Z",wait_for_trigger:"M12,9A2,2 0 0,1 10,7C10,5.89 10.9,5 12,5C13.11,5 14,5.89 14,7A2,2 0 0,1 12,9M12,14A2,2 0 0,1 10,12C10,10.89 10.9,10 12,10C13.11,10 14,10.89 14,12A2,2 0 0,1 12,14M12,19A2,2 0 0,1 10,17C10,15.89 10.9,15 12,15C13.11,15 14,15.89 14,17A2,2 0 0,1 12,19M20,10H17V8.86C18.72,8.41 20,6.86 20,5H17V4A1,1 0 0,0 16,3H8A1,1 0 0,0 7,4V5H4C4,6.86 5.28,8.41 7,8.86V10H4C4,11.86 5.28,13.41 7,13.86V15H4C4,16.86 5.28,18.41 7,18.86V20A1,1 0 0,0 8,21H16A1,1 0 0,0 17,20V18.86C18.72,18.41 20,16.86 20,15H17V13.86C18.72,13.41 20,11.86 20,10Z",repeat:a,repeat_count:a,repeat_while:a,repeat_until:a,repeat_for_each:a,choose:"M11,5H8L12,1L16,5H13V9.43C12.25,9.89 11.58,10.46 11,11.12V5M22,11L18,7V10C14.39,9.85 11.31,12.57 11,16.17C9.44,16.72 8.62,18.44 9.17,20C9.72,21.56 11.44,22.38 13,21.83C14.56,21.27 15.38,19.56 14.83,18C14.53,17.14 13.85,16.47 13,16.17C13.47,12.17 17.47,11.97 17.95,11.97V14.97L22,11M10.63,11.59C9.3,10.57 7.67,10 6,10V7L2,11L6,15V12C7.34,12.03 8.63,12.5 9.64,13.4C9.89,12.76 10.22,12.15 10.63,11.59Z",if:"M14,4L16.29,6.29L13.41,9.17L14.83,10.59L17.71,7.71L20,10V4M10,4H4V10L6.29,7.71L11,12.41V20H13V11.59L7.71,6.29",device_id:"M3 6H21V4H3C1.9 4 1 4.9 1 6V18C1 19.1 1.9 20 3 20H7V18H3V6M13 12H9V13.78C8.39 14.33 8 15.11 8 16C8 16.89 8.39 17.67 9 18.22V20H13V18.22C13.61 17.67 14 16.88 14 16S13.61 14.33 13 13.78V12M11 17.5C10.17 17.5 9.5 16.83 9.5 16S10.17 14.5 11 14.5 12.5 15.17 12.5 16 11.83 17.5 11 17.5M22 8H16C15.5 8 15 8.5 15 9V19C15 19.5 15.5 20 16 20H22C22.5 20 23 19.5 23 19V9C23 8.5 22.5 8 22 8M21 18H17V10H21V18Z",stop:"M13 24C9.74 24 6.81 22 5.6 19L2.57 11.37C2.26 10.58 3 9.79 3.81 10.05L4.6 10.31C5.16 10.5 5.62 10.92 5.84 11.47L7.25 15H8V3.25C8 2.56 8.56 2 9.25 2S10.5 2.56 10.5 3.25V12H11.5V1.25C11.5 .56 12.06 0 12.75 0S14 .56 14 1.25V12H15V2.75C15 2.06 15.56 1.5 16.25 1.5C16.94 1.5 17.5 2.06 17.5 2.75V12H18.5V5.75C18.5 5.06 19.06 4.5 19.75 4.5S21 5.06 21 5.75V16C21 20.42 17.42 24 13 24Z",sequence:"M7,13V11H21V13H7M7,19V17H21V19H7M7,7V5H21V7H7M3,8V5H2V4H4V8H3M2,17V16H5V20H2V19H4V18.5H3V17.5H4V17H2M4.25,10A0.75,0.75 0 0,1 5,10.75C5,10.95 4.92,11.14 4.79,11.27L3.12,13H5V14H2V13.08L4,11H2V10H4.25Z",parallel:"M16,4.5V7H5V9H16V11.5L19.5,8M16,12.5V15H5V17H16V19.5L19.5,16",variables:"M21 2H3C1.9 2 1 2.9 1 4V20C1 21.1 1.9 22 3 22H21C22.1 22 23 21.1 23 20V4C23 2.9 22.1 2 21 2M21 20H3V6H21V20M16.6 8C18.1 9.3 19 11.1 19 13C19 14.9 18.1 16.7 16.6 18L15 17.4C16.3 16.4 17 14.7 17 13S16.3 9.6 15 8.6L16.6 8M7.4 8L9 8.6C7.7 9.6 7 11.3 7 13S7.7 16.4 9 17.4L7.4 18C5.9 16.7 5 14.9 5 13S5.9 9.3 7.4 8M12.1 12L13.5 10H15L12.8 13L14.1 16H12.8L12 14L10.6 16H9L11.3 12.9L10 10H11.3L12.1 12Z",set_conversation_response:"M12,8H4A2,2 0 0,0 2,10V14A2,2 0 0,0 4,16H5V20A1,1 0 0,0 6,21H8A1,1 0 0,0 9,20V16H12L17,20V4L12,8M21.5,12C21.5,13.71 20.54,15.26 19,16V8C20.53,8.75 21.5,10.3 21.5,12Z"},n=new Set(["variables"]),s=[{groups:{device_id:{},dynamicGroups:{}}},{titleKey:"ui.panel.config.automation.editor.actions.groups.helpers.label",groups:{helpers:{}}},{titleKey:"ui.panel.config.automation.editor.actions.groups.other.label",groups:{event:{},service:{},set_conversation_response:{},other:{}}}],r={condition:{},delay:{},wait_template:{},wait_for_trigger:{},repeat_count:{},repeat_while:{},repeat_until:{},repeat_for_each:{},choose:{},if:{},stop:{},sequence:{},parallel:{},variables:{}},l={repeat_count:{repeat:{count:2,sequence:[]}},repeat_while:{repeat:{while:[],sequence:[]}},repeat_until:{repeat:{until:[],sequence:[]}},repeat_for_each:{repeat:{for_each:{},sequence:[]}}},c=["ha-automation-action-choose","ha-automation-action-condition","ha-automation-action-if","ha-automation-action-parallel","ha-automation-action-repeat","ha-automation-action-sequence"],d=["choose","if","parallel","sequence","repeat_while","repeat_until"],h=["repeat_count","repeat_for_each","wait_for_trigger"]},96707:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{u:function(){return b}});var o=i(31432),n=i(78261),s=(i(16280),i(50113),i(74423),i(62062),i(44114),i(18111),i(20116),i(61701),i(33110),i(5506),i(26099),i(55376)),r=i(88738),l=i(21754),c=i(16727),d=i(91889),h=i(39680),u=i(72125),p=i(53295),v=i(74687),_=i(22800),y=i(84125),f=i(29272),m=e([r,h,p]);[r,h,p]=m.then?(await m)():m;var g="ui.panel.config.automation.editor.actions.type",b=function(e,t,i,a,o,n){var s=arguments.length>6&&void 0!==arguments[6]&&arguments[6];try{var r=$(e,t,i,a,o,n,s);if("string"!=typeof r)throw new Error(String(r));return r}catch(c){console.error(c);var l="Error in describing action";return c.message&&(l+=": "+c.message),l}},$=function(e,t,i,a,m,b){var $=arguments.length>6&&void 0!==arguments[6]&&arguments[6];if(m.alias&&!$)return m.alias;if(b||(b=(0,f.pq)(m)),"service"===b){var A=m,w=[],M=A.target||A.data;if("string"==typeof M&&(0,u.F)(M))w.push(e.localize(`${g}.service.description.target_template`,{name:"target"}));else if(M)for(var k=0,C=Object.entries({area_id:"areas",device_id:"devices",entity_id:"entities",floor_id:"floors",label_id:"labels"});k<C.length;k++){var V=(0,n.A)(C[k],2),x=V[0],H=V[1];if(x in M){var S,L=(0,s.e)(M[x])||[],Z=(0,o.A)(L);try{var q=function(){var o=S.value;if((0,u.F)(o))return w.push(e.localize(`${g}.service.description.target_template`,{name:H})),1;if("entity_id"===x)if(o.includes(".")){var n=e.states[o];n?w.push((0,d.u)(n)):w.push(o)}else{var s=(0,_.P9)(t)[o];s?w.push((0,_.jh)(e,s)||o):"all"===o?w.push(e.localize(`${g}.service.description.target_every_entity`)):w.push(e.localize(`${g}.service.description.target_unknown_entity`))}else if("device_id"===x){var r=e.devices[o];r?w.push((0,c.T)(r,e)):w.push(e.localize(`${g}.service.description.target_unknown_device`))}else if("area_id"===x){var l=e.areas[o];null!=l&&l.name?w.push(l.name):w.push(e.localize(`${g}.service.description.target_unknown_area`))}else if("floor_id"===x){var h,p=null!==(h=a[o])&&void 0!==h?h:void 0;null!=p&&p.name?w.push(p.name):w.push(e.localize(`${g}.service.description.target_unknown_floor`))}else if("label_id"===x){var v=i.find((e=>e.label_id===o));null!=v&&v.name?w.push(v.name):w.push(e.localize(`${g}.service.description.target_unknown_label`))}else w.push(o)};for(Z.s();!(S=Z.n()).done&&!q(););}catch(he){Z.e(he)}finally{Z.f()}}}if(A.service_template||A.action&&(0,u.F)(A.action))return e.localize(w.length?`${g}.service.description.service_based_on_template`:`${g}.service.description.service_based_on_template_no_targets`,{targets:(0,h.c)(e.locale,w)});if(A.action){var O,z,E=A.action.split(".",2),I=(0,n.A)(E,2),P=I[0],j=I[1],B=null===(O=e.services[P])||void 0===O||null===(O=O[j])||void 0===O?void 0:O.description_placeholders,D=e.localize(`component.${P}.services.${j}.name`,B)||(null===(z=e.services[P])||void 0===z||null===(z=z[j])||void 0===z?void 0:z.name);return A.metadata?e.localize(w.length?`${g}.service.description.service_name`:`${g}.service.description.service_name_no_targets`,{domain:(0,y.p$)(e.localize,P),name:D||A.action,targets:(0,h.c)(e.locale,w)}):e.localize(w.length?`${g}.service.description.service_based_on_name`:`${g}.service.description.service_based_on_name_no_targets`,{name:D?`${(0,y.p$)(e.localize,P)}: ${D}`:A.action,targets:(0,h.c)(e.locale,w)})}return e.localize(`${g}.service.description.service`)}if("delay"===b){var R,F=m;return R="number"==typeof F.delay?e.localize(`${g}.delay.description.duration_string`,{string:(0,l.A)(F.delay)}):"string"==typeof F.delay?(0,u.F)(F.delay)?e.localize(`${g}.delay.description.duration_template`):e.localize(`${g}.delay.description.duration_string`,{string:F.delay||e.localize(`${g}.delay.description.duration_unknown`)}):F.delay?e.localize(`${g}.delay.description.duration_string`,{string:(0,r.nR)(e.locale,F.delay)}):e.localize(`${g}.delay.description.duration_string`,{string:e.localize(`${g}.delay.description.duration_unknown`)}),e.localize(`${g}.delay.description.full`,{duration:R})}if("wait_for_trigger"===b){var N=m,W=(0,s.e)(N.wait_for_trigger);return W&&0!==W.length?e.localize(`${g}.wait_for_trigger.description.wait_for_triggers`,{count:W.length}):e.localize(`${g}.wait_for_trigger.description.wait_for_a_trigger`)}if("variables"===b){var T=m;return e.localize(`${g}.variables.description.full`,{names:(0,h.c)(e.locale,Object.keys(T.variables))})}if("fire_event"===b){var K=m;return(0,u.F)(K.event)?e.localize(`${g}.event.description.full`,{name:e.localize(`${g}.event.description.template`)}):e.localize(`${g}.event.description.full`,{name:K.event})}if("wait_template"===b)return e.localize(`${g}.wait_template.description.full`);if("stop"===b){var U=m;return e.localize(`${g}.stop.description.full`,{hasReason:void 0!==U.stop?"true":"false",reason:U.stop})}if("if"===b)return void 0!==m.else?e.localize(`${g}.if.description.if_else`):e.localize(`${g}.if.description.if`);if("choose"===b){var Y=m;if(Y.choose){var G=(0,s.e)(Y.choose).length+(Y.default?1:0);return e.localize(`${g}.choose.description.full`,{number:G})}return e.localize(`${g}.choose.description.no_action`)}if("repeat"===b){var J=m,Q="";if("count"in J.repeat){var X=J.repeat.count;Q=e.localize(`${g}.repeat.description.count`,{count:X})}else if("while"in J.repeat){var ee=(0,s.e)(J.repeat.while);Q=e.localize(`${g}.repeat.description.while_count`,{count:ee.length})}else if("until"in J.repeat){var te=(0,s.e)(J.repeat.until);Q=e.localize(`${g}.repeat.description.until_count`,{count:te.length})}else if("for_each"in J.repeat){var ie=(0,s.e)(J.repeat.for_each).map((e=>JSON.stringify(e)));Q=e.localize(`${g}.repeat.description.for_each`,{items:(0,h.c)(e.locale,ie)})}return e.localize(`${g}.repeat.description.full`,{chosenAction:Q})}if("check_condition"===b)return e.localize(`${g}.check_condition.description.full`,{condition:(0,p.p)(m,e,t)});if("device_action"===b){var ae=m;if(!ae.device_id)return e.localize(`${g}.device_id.description.no_device`);var oe=(0,v.PV)(e,t,ae);if(oe)return oe;var ne=e.states[ae.entity_id];return ae.type?`${ae.type} ${ne?(0,d.u)(ne):ae.entity_id}`:e.localize(`${g}.device_id.description.perform_device_action`,{device:ne?(0,d.u)(ne):ae.entity_id})}if("sequence"===b){var se=m,re=(0,s.e)(se.sequence).length;return e.localize(`${g}.sequence.description.full`,{number:re})}if("parallel"===b){var le=m,ce=(0,s.e)(le.parallel).length;return e.localize(`${g}.parallel.description.full`,{number:ce})}if("set_conversation_response"===b){var de=m;return(0,u.F)(de.set_conversation_response)?e.localize(`${g}.set_conversation_response.description.template`):e.localize(`${g}.set_conversation_response.description.full`,{response:de.set_conversation_response})}return b};a()}catch(A){a(A)}}))},34216:function(e,t,i){i.d(t,{d:function(){return a}});i(74423);var a=(e,t)=>e.callWS({type:"execute_script",sequence:t})},30538:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(62826)),l=i(96196),c=i(77845),d=i(94333),h=i(51757),u=i(92542),p=i(23362),v=i(265),_=i(29272),y=(i(13295),i(36857)),f=i(7),m=e([p,f]);[p,f]=m.then?(await m)():m;var g,b,$,A,w=e=>e,M=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e.yamlMode=!1,e.indent=!1,e.selected=!1,e.narrow=!1,e.inSidebar=!1,e.uiSupported=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e=this.yamlMode||!this.uiSupported,t=(0,f.MS)(this.action);return(0,l.qy)(g||(g=w`
      <div
        class=${0}
      >
        ${0}
      </div>
    `),(0,d.H)({"card-content":!0,disabled:!this.indent&&(this.disabled||!1===this.action.enabled&&!this.yamlMode),yaml:e,indent:this.indent,card:!this.inSidebar}),e?(0,l.qy)(b||(b=w`
              ${0}
              <ha-yaml-editor
                .hass=${0}
                .defaultValue=${0}
                @value-changed=${0}
                .readOnly=${0}
              ></ha-yaml-editor>
            `),this.uiSupported?l.s6:(0,l.qy)($||($=w`
                    <ha-automation-editor-warning
                      .alertTitle=${0}
                      .localize=${0}
                    ></ha-automation-editor-warning>
                  `),this.hass.localize("ui.panel.config.automation.editor.actions.unsupported_action"),this.hass.localize),this.hass,this.action,this._onYamlChange,this.disabled):(0,l.qy)(A||(A=w`
              <div @value-changed=${0}>
                ${0}
              </div>
            `),this._onUiChanged,(0,h._)(`ha-automation-action-${t}`,{hass:this.hass,action:this.action,disabled:this.disabled,narrow:this.narrow,optionsInSidebar:this.indent,indent:this.indent,inSidebar:this.inSidebar})))}},{key:"_onYamlChange",value:function(e){e.stopPropagation(),e.detail.isValid&&(0,u.r)(this,this.inSidebar?"yaml-changed":"value-changed",{value:(0,_.Rn)(e.detail.value)})}},{key:"_onUiChanged",value:function(e){e.stopPropagation();var t=Object.assign(Object.assign({},this.action.alias?{alias:this.action.alias}:{}),e.detail.value);(0,u.r)(this,"value-changed",{value:t})}},{key:"expandAll",value:function(){var e,t;null===(e=this._collapsibleElement)||void 0===e||null===(t=e.expandAll)||void 0===t||t.call(e)}},{key:"collapseAll",value:function(){var e,t;null===(e=this._collapsibleElement)||void 0===e||null===(t=e.collapseAll)||void 0===t||t.call(e)}}])}(l.WF);M.styles=[y.yj,y.aM],(0,r.__decorate)([(0,c.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],M.prototype,"action",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],M.prototype,"yamlMode",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],M.prototype,"indent",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean,reflect:!0})],M.prototype,"selected",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],M.prototype,"narrow",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean,attribute:"sidebar"})],M.prototype,"inSidebar",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean,attribute:"supported"})],M.prototype,"uiSupported",void 0),(0,r.__decorate)([(0,c.P)("ha-yaml-editor")],M.prototype,"yamlEditor",void 0),(0,r.__decorate)([(0,c.P)(v.MC.join(", "))],M.prototype,"_collapsibleElement",void 0),M=(0,r.__decorate)([(0,c.EM)("ha-automation-action-editor")],M),t()}catch(k){t(k)}}))},7:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{MS:function(){return $e},Pb:function(){return Ae}});var o=i(94741),n=i(61397),s=i(50264),r=i(44734),l=i(56038),c=i(75864),d=i(69683),h=i(6454),u=i(25460),p=(i(28706),i(50113),i(74423),i(18111),i(20116),i(13579),i(26099),i(62826)),v=i(16527),_=i(34271),y=i(53289),f=i(96196),m=i(77845),g=i(22786),b=i(55376),$=i(42256),A=i(92542),w=i(91737),M=i(55124),k=i(74522),C=i(91225),V=i(4657),x=(i(27639),i(95379),i(34811),i(60733),i(63419),i(32072),i(99892),i(63426)),H=i(88422),S=i(265),L=i(10038),Z=i(34485),q=i(34972),O=i(29272),z=i(96707),E=i(34216),I=i(10234),P=i(98315),j=i(4848),B=(i(13295),i(36857)),D=i(30538),R=i(84648),F=i(23556),N=(i(17550),i(84915)),W=i(49217),T=i(36742),K=i(83230),U=i(73118),Y=i(14396),G=i(11042),J=(i(47961),i(11553),i(31267)),Q=(i(2117),e([x,H,D,R,F,N,W,T,K,Y,G,J,z,U]));[x,H,D,R,F,N,W,T,K,Y,G,J,z,U]=Q.then?(await Q)():Q;var X,ee,te,ie,ae,oe,ne,se,re,le,ce,de,he,ue,pe,ve,_e,ye,fe,me,ge=e=>e,be="M6,2A4,4 0 0,1 10,6V8H14V6A4,4 0 0,1 18,2A4,4 0 0,1 22,6A4,4 0 0,1 18,10H16V14H18A4,4 0 0,1 22,18A4,4 0 0,1 18,22A4,4 0 0,1 14,18V16H10V18A4,4 0 0,1 6,22A4,4 0 0,1 2,18A4,4 0 0,1 6,14H8V10H6A4,4 0 0,1 2,6A4,4 0 0,1 6,2M16,18A2,2 0 0,0 18,20A2,2 0 0,0 20,18A2,2 0 0,0 18,16H16V18M14,10H10V14H14V10M6,16A2,2 0 0,0 4,18A2,2 0 0,0 6,20A2,2 0 0,0 8,18V16H6M8,6A2,2 0 0,0 6,4A2,2 0 0,0 4,6A2,2 0 0,0 6,8H8V6M18,8A2,2 0 0,0 20,6A2,2 0 0,0 18,4A2,2 0 0,0 16,6V8H18Z",$e=(0,g.A)((e=>{if(e)return"action"in e?(0,O.pq)(e):L.I8.some((t=>t in e))?"condition":Object.keys(S.O$).find((t=>t in e))})),Ae=(e,t)=>{var i,a;t.stopPropagation();var o=null===(i=t.target)||void 0===i?void 0:i.name;if(o){var n,s=(null===(a=t.detail)||void 0===a?void 0:a.value)||t.target.value;if((e.action[o]||"")!==s)s?n=Object.assign(Object.assign({},e.action),{},{[o]:s}):delete(n=Object.assign({},e.action))[o],(0,A.r)(e,"value-changed",{value:n})}},we=function(e){function t(){var e;(0,r.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,d.A)(this,t,[].concat(a))).narrow=!1,e.disabled=!1,e.root=!1,e.optionsInSidebar=!1,e.sortSelected=!1,e._uiModeAvailable=!0,e._yamlMode=!1,e._selected=!1,e._collapsed=!0,e._onDisable=()=>{var t,i,a=!(null===(t=e.action.enabled)||void 0===t||t),o=Object.assign(Object.assign({},e.action),{},{enabled:a});((0,A.r)((0,c.A)(e),"value-changed",{value:o}),e._selected&&e.optionsInSidebar&&e.openSidebar(o),e._yamlMode&&!e.optionsInSidebar)&&(null===(i=e._actionEditor)||void 0===i||null===(i=i.yamlEditor)||void 0===i||i.setValue(o))},e._runAction=(0,s.A)((0,n.A)().m((function t(){var i,a;return(0,n.A)().w((function(t){for(;;)switch(t.p=t.n){case 0:return requestAnimationFrame((()=>{e.scrollIntoViewIfNeeded?e.scrollIntoViewIfNeeded():e.scrollIntoView()})),t.n=1,(0,Z.$)(e.hass,{actions:e.action});case 1:if((i=t.v).actions.valid){t.n=2;break}return(0,I.K$)((0,c.A)(e),{title:e.hass.localize("ui.panel.config.automation.editor.actions.invalid_action"),text:i.actions.error}),t.a(2);case 2:return t.p=2,t.n=3,(0,E.d)(e.hass,e.action);case 3:t.n=5;break;case 4:return t.p=4,a=t.v,(0,I.K$)((0,c.A)(e),{title:e.hass.localize("ui.panel.config.automation.editor.actions.run_action_error"),text:a.message||a}),t.a(2);case 5:(0,j.P)((0,c.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.actions.run_action_success")});case 6:return t.a(2)}}),t,null,[[2,4]])}))),e._onDelete=()=>{(0,A.r)((0,c.A)(e),"value-changed",{value:null}),e._selected&&(0,A.r)((0,c.A)(e),"close-sidebar"),(0,j.P)((0,c.A)(e),{message:e.hass.localize("ui.common.successfully_deleted"),duration:4e3,action:{text:e.hass.localize("ui.common.undo"),action:()=>{(0,A.r)(window,"undo-change")}}})},e._renameAction=(0,s.A)((0,n.A)().m((function t(){var i,a,o;return(0,n.A)().w((function(t){for(;;)switch(t.n){case 0:return t.n=1,(0,I.an)((0,c.A)(e),{title:e.hass.localize("ui.panel.config.automation.editor.actions.change_alias"),inputLabel:e.hass.localize("ui.panel.config.automation.editor.actions.alias"),inputType:"string",placeholder:(0,k.Z)((0,z.u)(e.hass,e._entityReg,e._labelReg,e._floorReg,e.action,void 0,!0)),defaultValue:e.action.alias,confirmText:e.hass.localize("ui.common.submit")});case 1:null!==(i=t.v)&&(a=Object.assign({},e.action),""===i?delete a.alias:a.alias=i,(0,A.r)((0,c.A)(e),"value-changed",{value:a}),e._selected&&e.optionsInSidebar?e.openSidebar(a):e._yamlMode&&(null===(o=e._actionEditor)||void 0===o||null===(o=o.yamlEditor)||void 0===o||o.setValue(a)));case 2:return t.a(2)}}),t)}))),e._duplicateAction=()=>{(0,A.r)((0,c.A)(e),"duplicate")},e._insertAfter=t=>!(0,b.e)(t).some((e=>!(0,O.ve)(e)))&&((0,A.r)((0,c.A)(e),"insert-after",{value:t}),!0),e._copyAction=()=>{e._setClipboard(),(0,j.P)((0,c.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.actions.copied_to_clipboard"),duration:2e3})},e._cutAction=()=>{e._setClipboard(),(0,A.r)((0,c.A)(e),"value-changed",{value:null}),e._selected&&(0,A.r)((0,c.A)(e),"close-sidebar"),(0,j.P)((0,c.A)(e),{message:e.hass.localize("ui.panel.config.automation.editor.actions.cut_to_clipboard"),duration:2e3})},e._moveUp=()=>{(0,A.r)((0,c.A)(e),"move-up")},e._moveDown=()=>{(0,A.r)((0,c.A)(e),"move-down")},e._toggleYamlMode=t=>{e._yamlMode?e._switchUiMode():e._switchYamlMode(),e.optionsInSidebar?t&&e.openSidebar():e.expand()},e._uiSupported=(0,g.A)((e=>void 0!==customElements.get(`ha-automation-action-${e}`))),e}return(0,h.A)(t,e),(0,l.A)(t,[{key:"selected",get:function(){return this._selected}},{key:"firstUpdated",value:function(e){(0,u.A)(t,"firstUpdated",this,3)([e]),this.root&&(this._collapsed=!1)}},{key:"willUpdate",value:function(e){if(e.has("yamlMode")&&(this._warnings=void 0),e.has("action")){var t=$e(this.action);this._uiModeAvailable=void 0!==t&&!S.ix.has(t),this._uiModeAvailable||this._yamlMode||(this._yamlMode=!0)}}},{key:"_renderOverflowLabel",value:function(e,t){return(0,f.qy)(X||(X=ge`
      <div class="overflow-label">
        ${0}
        ${0}
      </div>
    `),e,this.optionsInSidebar&&!this.narrow?t||(0,f.qy)(ee||(ee=ge`<span
              class="shortcut-placeholder ${0}"
            ></span>`),P.c?"mac":""):f.s6)}},{key:"_renderRow",value:function(){var e=$e(this.action);return(0,f.qy)(te||(te=ge`
      ${0}
      <h3 slot="header">
        ${0}
      </h3>

      <slot name="icons" slot="icons"></slot>

      ${0}

      <ha-md-button-menu
        quick
        slot="icons"
        @click=${0}
        @keydown=${0}
        @closed=${0}
        positioning="fixed"
        anchor-corner="end-end"
        menu-corner="start-end"
      >
        <ha-icon-button
          slot="trigger"
          .label=${0}
          .path=${0}
        ></ha-icon-button>

        <ha-md-menu-item .clickAction=${0}>
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>
        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>
        <ha-md-divider role="separator" tabindex="-1"></ha-md-divider>
        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon
            slot="start"
            .path=${0}
          ></ha-svg-icon>

          ${0}
        </ha-md-menu-item>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        ${0}

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
          ${0}
        </ha-md-menu-item>

        <ha-md-divider role="separator" tabindex="-1"></ha-md-divider>

        <ha-md-menu-item
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon
            slot="start"
            .path=${0}
          ></ha-svg-icon>

          ${0}
        </ha-md-menu-item>
        <ha-md-menu-item
          class="warning"
          .clickAction=${0}
          .disabled=${0}
        >
          <ha-svg-icon
            class="warning"
            slot="start"
            .path=${0}
          ></ha-svg-icon>

          ${0}
        </ha-md-menu-item>
      </ha-md-button-menu>

      ${0}
    `),"service"===e&&"action"in this.action&&this.action.action?(0,f.qy)(ie||(ie=ge`
            <ha-service-icon
              slot="leading-icon"
              class="action-icon"
              .hass=${0}
              .service=${0}
            ></ha-service-icon>
          `),this.hass,this.action.action):(0,f.qy)(ae||(ae=ge`
            <ha-svg-icon
              slot="leading-icon"
              class="action-icon"
              .path=${0}
            ></ha-svg-icon>
          `),S.O$[e]),(0,k.Z)((0,z.u)(this.hass,this._entityReg,this._labelReg,this._floorReg,this.action)),"condition"!==e&&!0===this.action.continue_on_error?(0,f.qy)(oe||(oe=ge`<ha-svg-icon
              id="svg-icon"
              slot="icons"
              .path=${0}
            ></ha-svg-icon>
            <ha-tooltip for="svg-icon">
              ${0}
            </ha-tooltip>`),"M18.75 22.16L16 19.16L17.16 18L18.75 19.59L22.34 16L23.5 17.41L18.75 22.16M13 13V7H11V13H13M13 17V15H11V17H13M12 2C17.5 2 22 6.5 22 12L21.91 13.31C21.31 13.11 20.67 13 20 13C16.69 13 14 15.69 14 19C14 19.95 14.22 20.85 14.62 21.65C13.78 21.88 12.91 22 12 22C6.5 22 2 17.5 2 12C2 6.5 6.5 2 12 2Z",this.hass.localize("ui.panel.config.automation.editor.actions.continue_on_error")):f.s6,w.C,M.d,M.d,this.hass.localize("ui.common.menu"),"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this._runAction,"M8,5.14V19.14L19,12.14L8,5.14Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.run")),this._renameAction,this.disabled,"M18,17H10.5L12.5,15H18M6,17V14.5L13.88,6.65C14.07,6.45 14.39,6.45 14.59,6.65L16.35,8.41C16.55,8.61 16.55,8.92 16.35,9.12L8.47,17M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.rename")),this._duplicateAction,this.disabled,"M16,8H14V11H11V13H14V16H16V13H19V11H16M2,12C2,9.21 3.64,6.8 6,5.68V3.5C2.5,4.76 0,8.09 0,12C0,15.91 2.5,19.24 6,20.5V18.32C3.64,17.2 2,14.79 2,12M15,3C10.04,3 6,7.04 6,12C6,16.96 10.04,21 15,21C19.96,21 24,16.96 24,12C24,7.04 19.96,3 15,3M15,19C11.14,19 8,15.86 8,12C8,8.14 11.14,5 15,5C18.86,5 22,8.14 22,12C22,15.86 18.86,19 15,19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.duplicate")),this._copyAction,this.disabled,"M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.copy"),(0,f.qy)(ne||(ne=ge`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span>C</span>
            </span>`),P.c?(0,f.qy)(se||(se=ge`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),be):this.hass.localize("ui.panel.config.automation.editor.ctrl"))),this._cutAction,this.disabled,"M19,3L13,9L15,11L22,4V3M12,12.5A0.5,0.5 0 0,1 11.5,12A0.5,0.5 0 0,1 12,11.5A0.5,0.5 0 0,1 12.5,12A0.5,0.5 0 0,1 12,12.5M6,20A2,2 0 0,1 4,18C4,16.89 4.9,16 6,16A2,2 0 0,1 8,18C8,19.11 7.1,20 6,20M6,8A2,2 0 0,1 4,6C4,4.89 4.9,4 6,4A2,2 0 0,1 8,6C8,7.11 7.1,8 6,8M9.64,7.64C9.87,7.14 10,6.59 10,6A4,4 0 0,0 6,2A4,4 0 0,0 2,6A4,4 0 0,0 6,10C6.59,10 7.14,9.87 7.64,9.64L10,12L7.64,14.36C7.14,14.13 6.59,14 6,14A4,4 0 0,0 2,18A4,4 0 0,0 6,22A4,4 0 0,0 10,18C10,17.41 9.87,16.86 9.64,16.36L12,14L19,21H22V20L9.64,7.64Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.cut"),(0,f.qy)(re||(re=ge`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span>X</span>
            </span>`),P.c?(0,f.qy)(le||(le=ge`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),be):this.hass.localize("ui.panel.config.automation.editor.ctrl"))),this.optionsInSidebar?f.s6:(0,f.qy)(ce||(ce=ge`
              <ha-md-menu-item
                .clickAction=${0}
                .disabled=${0}
              >
                ${0}
                <ha-svg-icon slot="start" .path=${0}></ha-svg-icon
              ></ha-md-menu-item>
              <ha-md-menu-item
                .clickAction=${0}
                .disabled=${0}
              >
                ${0}
                <ha-svg-icon slot="start" .path=${0}></ha-svg-icon
              ></ha-md-menu-item>
            `),this._moveUp,this.disabled||!!this.first,this.hass.localize("ui.panel.config.automation.editor.move_up"),"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",this._moveDown,this.disabled||!!this.last,this.hass.localize("ui.panel.config.automation.editor.move_down"),"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"),this._toggleYamlMode,!this._uiModeAvailable||!!this._warnings,"M3 6V8H14V6H3M3 10V12H14V10H3M20 10.1C19.9 10.1 19.7 10.2 19.6 10.3L18.6 11.3L20.7 13.4L21.7 12.4C21.9 12.2 21.9 11.8 21.7 11.6L20.4 10.3C20.3 10.2 20.2 10.1 20 10.1M18.1 11.9L12 17.9V20H14.1L20.2 13.9L18.1 11.9M3 14V16H10V14H3Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.edit_"+(this._yamlMode?"ui":"yaml"))),this._onDisable,this.disabled,!1===this.action.enabled?"M12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M10,16.5L16,12L10,7.5V16.5Z":"M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4C16.41,4 20,7.59 20,12C20,16.41 16.41,20 12,20C7.59,20 4,16.41 4,12C4,7.59 7.59,4 12,4M9,9V15H15V9",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions."+(!1===this.action.enabled?"enable":"disable"))),this._onDelete,this.disabled,"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.delete"),(0,f.qy)(de||(de=ge`<span class="shortcut">
              <span
                >${0}</span
              >
              <span>+</span>
              <span
                >${0}</span
              >
            </span>`),P.c?(0,f.qy)(he||(he=ge`<ha-svg-icon
                      slot="start"
                      .path=${0}
                    ></ha-svg-icon>`),be):this.hass.localize("ui.panel.config.automation.editor.ctrl"),this.hass.localize("ui.panel.config.automation.editor.del"))),this.optionsInSidebar?f.s6:(0,f.qy)(ue||(ue=ge`${0}
            <ha-automation-action-editor
              .hass=${0}
              .action=${0}
              .disabled=${0}
              .yamlMode=${0}
              .narrow=${0}
              .uiSupported=${0}
              @ui-mode-not-available=${0}
            ></ha-automation-action-editor>`),this._warnings?(0,f.qy)(pe||(pe=ge`<ha-automation-editor-warning
                  .localize=${0}
                  .warnings=${0}
                >
                </ha-automation-editor-warning>`),this.hass.localize,this._warnings):f.s6,this.hass,this.action,this.disabled,this._yamlMode,this.narrow,this._uiSupported(e),this._handleUiModeNotAvailable))}},{key:"render",value:function(){if(!this.action)return f.s6;var e=$e(this.action),t="repeat"===e?`repeat_${(0,U.m)(this.action.repeat)}`:e;return(0,f.qy)(ve||(ve=ge`
      <ha-card outlined>
        ${0}
        ${0}
      </ha-card>

      ${0}
    `),!1===this.action.enabled?(0,f.qy)(_e||(_e=ge`
              <div class="disabled-bar">
                ${0}
              </div>
            `),this.hass.localize("ui.panel.config.automation.editor.actions.disabled")):f.s6,this.optionsInSidebar?(0,f.qy)(ye||(ye=ge`<ha-automation-row
              .disabled=${0}
              .leftChevron=${0}
              .collapsed=${0}
              .selected=${0}
              .highlight=${0}
              .buildingBlock=${0}
              .sortSelected=${0}
              @click=${0}
              @toggle-collapsed=${0}
              >${0}</ha-automation-row
            >`),!1===this.action.enabled,[].concat((0,o.A)(S.L_),(0,o.A)(S.I8)).includes(t)||"condition"===t&&L.I8.includes(this.action.condition),this._collapsed,this._selected,this.highlight,[].concat((0,o.A)(S.L_),(0,o.A)(S.I8)).includes(t),this.sortSelected,this._toggleSidebar,this._toggleCollapse,this._renderRow()):(0,f.qy)(fe||(fe=ge`
              <ha-expansion-panel left-chevron>
                ${0}
              </ha-expansion-panel>
            `),this._renderRow()),this.optionsInSidebar&&([].concat((0,o.A)(S.L_),(0,o.A)(S.I8)).includes(t)||"condition"===t&&L.I8.includes(this.action.condition))?(0,f.qy)(me||(me=ge`<ha-automation-action-editor
            class=${0}
            .hass=${0}
            .action=${0}
            .narrow=${0}
            .disabled=${0}
            .uiSupported=${0}
            indent
            .selected=${0}
            @value-changed=${0}
          ></ha-automation-action-editor>`),this._collapsed?"hidden":"",this.hass,this.action,this.narrow,this.disabled,this._uiSupported(e),this._selected,this._onValueChange):f.s6)}},{key:"_onValueChange",value:function(e){this._selected&&this.optionsInSidebar&&this.openSidebar(e.detail.value)}},{key:"_setClipboard",value:function(){this._clipboard=Object.assign(Object.assign({},this._clipboard),{},{action:(0,_.A)(this.action)});var e=this.action;"sequence"in e&&(e=Object.assign(Object.assign({},this.action),{},{metadata:{}})),(0,V.l)((0,y.Bh)(e))}},{key:"_switchUiMode",value:function(){this._yamlMode=!1}},{key:"_switchYamlMode",value:function(){this._yamlMode=!0}},{key:"_handleUiModeNotAvailable",value:function(e){this._warnings=(0,C._)(this.hass,e.detail).warnings,this._yamlMode||(this._yamlMode=!0)}},{key:"_toggleSidebar",value:function(e){null==e||e.stopPropagation(),this._selected?(0,A.r)(this,"request-close-sidebar"):this.openSidebar()}},{key:"openSidebar",value:function(e){var t=null!=e?e:this.action,i=$e(t);(0,A.r)(this,"open-sidebar",{save:e=>{(0,A.r)(this,"value-changed",{value:e})},close:e=>{this._selected=!1,(0,A.r)(this,"close-sidebar"),e&&this.focus()},rename:()=>{this._renameAction()},toggleYamlMode:()=>{this._toggleYamlMode(),this.openSidebar()},disable:this._onDisable,delete:this._onDelete,copy:this._copyAction,cut:this._cutAction,duplicate:this._duplicateAction,insertAfter:this._insertAfter,run:this._runAction,config:{action:t},uiSupported:!!i&&this._uiSupported(i),yamlMode:this._yamlMode}),this._selected=!0,this._collapsed=!1,this.narrow&&window.setTimeout((()=>{this.scrollIntoView({block:"start",behavior:"smooth"})}),180)}},{key:"expand",value:function(){this.optionsInSidebar?this._collapsed=!1:this.updateComplete.then((()=>{this.shadowRoot.querySelector("ha-expansion-panel").expanded=!0}))}},{key:"collapse",value:function(){this.optionsInSidebar?this._collapsed=!0:this.updateComplete.then((()=>{this.shadowRoot.querySelector("ha-expansion-panel").expanded=!1}))}},{key:"expandAll",value:function(){var e;this.expand(),null===(e=this._actionEditor)||void 0===e||e.expandAll()}},{key:"collapseAll",value:function(){var e;this.collapse(),null===(e=this._actionEditor)||void 0===e||e.collapseAll()}},{key:"_toggleCollapse",value:function(){this._collapsed=!this._collapsed}},{key:"focus",value:function(){var e;null===(e=this._automationRowElement)||void 0===e||e.focus()}}])}(f.WF);we.styles=[B.bH,B.Lt],(0,p.__decorate)([(0,m.MZ)({attribute:!1})],we.prototype,"hass",void 0),(0,p.__decorate)([(0,m.MZ)({attribute:!1})],we.prototype,"action",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"narrow",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"disabled",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"root",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"first",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"last",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean})],we.prototype,"highlight",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean,attribute:"sidebar"})],we.prototype,"optionsInSidebar",void 0),(0,p.__decorate)([(0,m.MZ)({type:Boolean,attribute:"sort-selected"})],we.prototype,"sortSelected",void 0),(0,p.__decorate)([(0,$.I)({key:"automationClipboard",state:!1,subscribe:!0,storage:"sessionStorage"})],we.prototype,"_clipboard",void 0),(0,p.__decorate)([(0,m.wk)(),(0,v.Fg)({context:q.ih,subscribe:!0})],we.prototype,"_entityReg",void 0),(0,p.__decorate)([(0,m.wk)(),(0,v.Fg)({context:q.HD,subscribe:!0})],we.prototype,"_labelReg",void 0),(0,p.__decorate)([(0,m.wk)(),(0,v.Fg)({context:q.rf,subscribe:!0})],we.prototype,"_floorReg",void 0),(0,p.__decorate)([(0,m.wk)()],we.prototype,"_uiModeAvailable",void 0),(0,p.__decorate)([(0,m.wk)()],we.prototype,"_yamlMode",void 0),(0,p.__decorate)([(0,m.wk)()],we.prototype,"_selected",void 0),(0,p.__decorate)([(0,m.wk)()],we.prototype,"_collapsed",void 0),(0,p.__decorate)([(0,m.wk)()],we.prototype,"_warnings",void 0),(0,p.__decorate)([(0,m.P)("ha-automation-action-editor")],we.prototype,"_actionEditor",void 0),(0,p.__decorate)([(0,m.P)("ha-automation-row")],we.prototype,"_automationRowElement",void 0),we=(0,p.__decorate)([(0,m.EM)("ha-automation-action-row")],we),a()}catch(Me){a(Me)}}))},10754:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(94741),o=i(61397),n=i(50264),s=i(44734),r=i(56038),l=i(75864),c=i(69683),d=i(6454),h=i(25460),u=(i(28706),i(2008),i(74423),i(23792),i(34782),i(54554),i(71658),i(18111),i(22489),i(7588),i(26099),i(38781),i(73772),i(23500),i(62953),i(62826)),p=i(34271),v=i(96196),_=i(77845),y=i(4937),f=i(55376),m=i(42256),g=i(92542),b=i(55124),$=i(99034),A=i(89473),w=(i(63801),i(60961),i(265)),M=i(80812),k=i(78232),C=i(36857),V=i(7),x=e([A,V]);[A,V]=x.then?(await x)():x;var H,S,L,Z=e=>e,q=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,c.A)(this,t,[].concat(a))).narrow=!1,e.disabled=!1,e.root=!1,e.optionsInSidebar=!1,e._focusLastActionOnChange=!1,e._actionKeys=new WeakMap,e._addAction=(t,i)=>{var a;if(t===k.u)a=e.actions.concat((0,p.A)(e._clipboard.action));else if(t in w.EN)a=e.actions.concat(w.EN[t]);else if((0,M.Q)(t))a=e.actions.concat({action:(0,M.Dt)(t),metadata:{},target:i});else{var o=customElements.get(`ha-automation-action-${t}`);a=e.actions.concat(o?Object.assign({},o.defaultConfig):{[t]:{}})}e._focusLastActionOnChange=!0,(0,g.r)((0,l.A)(e),"value-changed",{value:a})},e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,v.qy)(H||(H=Z`
      <ha-sortable
        handle-selector=".handle"
        draggable-selector="ha-automation-action-row"
        .disabled=${0}
        group="actions"
        invert-swap
        @item-moved=${0}
        @item-added=${0}
        @item-removed=${0}
      >
        <div class="rows ${0}">
          ${0}
          <div class="buttons">
            <ha-button
              .disabled=${0}
              @click=${0}
              .appearance=${0}
              .size=${0}
            >
              <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
              ${0}
            </ha-button>
          </div>
        </div>
      </ha-sortable>
    `),this.disabled,this._actionMoved,this._actionAdded,this._actionRemoved,this.optionsInSidebar?"":"no-sidebar",(0,y.u)(this.actions,(e=>this._getKey(e)),((e,t)=>{var i;return(0,v.qy)(S||(S=Z`
              <ha-automation-action-row
                .root=${0}
                .sortableData=${0}
                .index=${0}
                .first=${0}
                .last=${0}
                .action=${0}
                .narrow=${0}
                .disabled=${0}
                @duplicate=${0}
                @insert-after=${0}
                @move-down=${0}
                @move-up=${0}
                @value-changed=${0}
                .hass=${0}
                .highlight=${0}
                .optionsInSidebar=${0}
                .sortSelected=${0}
                @stop-sort-selection=${0}
              >
                ${0}
              </ha-automation-action-row>
            `),this.root,e,t,0===t,t===this.actions.length-1,e,this.narrow,this.disabled,this._duplicateAction,this._insertAfter,this._moveDown,this._moveUp,this._actionChanged,this.hass,null===(i=this.highlightedActions)||void 0===i?void 0:i.includes(e),this.optionsInSidebar,this._rowSortSelected===t,this._stopSortSelection,this.disabled?v.s6:(0,v.qy)(L||(L=Z`
                      <div
                        tabindex="0"
                        class="handle ${0}"
                        slot="icons"
                        @keydown=${0}
                        @click=${0}
                        .index=${0}
                      >
                        <ha-svg-icon
                          .path=${0}
                        ></ha-svg-icon>
                      </div>
                    `),this._rowSortSelected===t?"active":"",this._handleDragKeydown,b.d,t,"M21 11H3V9H21V11M21 13H3V15H21V13Z"))})),this.disabled,this._addActionDialog,this.root?"accent":"filled",this.root?"medium":"small","M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",this.hass.localize("ui.panel.config.automation.editor.actions.add"))}},{key:"updated",value:function(e){if((0,h.A)(t,"updated",this,3)([e]),e.has("actions")&&(this._focusLastActionOnChange||void 0!==this._focusActionIndexOnChange)){var i=this._focusLastActionOnChange?"new":"moved",a=this.shadowRoot.querySelector("ha-automation-action-row:"+("new"===i?"last-of-type":`nth-of-type(${this._focusActionIndexOnChange+1})`));this._focusLastActionOnChange=!1,this._focusActionIndexOnChange=void 0,a.updateComplete.then((()=>{var e=(0,V.MS)(a.action);!e||!this.optionsInSidebar||w.L_.includes(e)&&"moved"!==i||(a.openSidebar(),this.narrow&&a.scrollIntoView({block:"start",behavior:"smooth"})),"new"===i&&a.expand(),this.optionsInSidebar||a.focus()}))}}},{key:"expandAll",value:function(){var e;null===(e=this._actionRowElements)||void 0===e||e.forEach((e=>{e.expandAll()}))}},{key:"collapseAll",value:function(){var e;null===(e=this._actionRowElements)||void 0===e||e.forEach((e=>{e.collapseAll()}))}},{key:"_addActionDialog",value:function(){var e;this.narrow&&(0,g.r)(this,"request-close-sidebar"),(0,k.g)(this,{type:"action",add:this._addAction,clipboardItem:(0,V.MS)(null===(e=this._clipboard)||void 0===e?void 0:e.action)})}},{key:"_getKey",value:function(e){return this._actionKeys.has(e)||this._actionKeys.set(e,Math.random().toString()),this._actionKeys.get(e)}},{key:"_moveUp",value:(m=(0,n.A)((0,o.A)().m((function e(t){var i,a;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:t.stopPropagation(),i=t.target.index,t.target.first||(a=i-1,this._move(i,a),this._rowSortSelected===i&&(this._rowSortSelected=a),t.target.focus());case 1:return e.a(2)}}),e,this)}))),function(e){return m.apply(this,arguments)})},{key:"_moveDown",value:(_=(0,n.A)((0,o.A)().m((function e(t){var i,a;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:t.stopPropagation(),i=t.target.index,t.target.last||(a=i+1,this._move(i,a),this._rowSortSelected===i&&(this._rowSortSelected=a),t.target.focus());case 1:return e.a(2)}}),e,this)}))),function(e){return _.apply(this,arguments)})},{key:"_move",value:function(e,t){var i=this.actions.concat(),a=i.splice(e,1)[0];i.splice(t,0,a),this.actions=i,(0,g.r)(this,"value-changed",{value:i})}},{key:"_actionMoved",value:function(e){e.stopPropagation();var t=e.detail,i=t.oldIndex,a=t.newIndex;this._move(i,a)}},{key:"_actionAdded",value:(u=(0,n.A)((0,o.A)().m((function e(t){var i,n,s,r,l,c;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail,n=i.index,s=i.data,r=t.detail.item,l=r.selected,c=[].concat((0,a.A)(this.actions.slice(0,n)),[s],(0,a.A)(this.actions.slice(n))),this.actions=c,l&&(this._focusActionIndexOnChange=1===c.length?0:n),e.n=1,(0,$.E)();case 1:this.actions!==c&&(c=[].concat((0,a.A)(this.actions.slice(0,n)),[s],(0,a.A)(this.actions.slice(n))),l&&(this._focusActionIndexOnChange=1===c.length?0:n)),(0,g.r)(this,"value-changed",{value:c});case 2:return e.a(2)}}),e,this)}))),function(e){return u.apply(this,arguments)})},{key:"_actionRemoved",value:(i=(0,n.A)((0,o.A)().m((function e(t){var i,a,n;return(0,o.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail.index,a=this.actions[i],this.actions=this.actions.filter((e=>e!==a)),e.n=1,(0,$.E)();case 1:n=this.actions.filter((e=>e!==a)),(0,g.r)(this,"value-changed",{value:n});case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_actionChanged",value:function(e){e.stopPropagation();var t=(0,a.A)(this.actions),i=e.detail.value,o=e.target.index;if(null===i)t.splice(o,1);else{var n=this._getKey(t[o]);this._actionKeys.set(i,n),t[o]=i}(0,g.r)(this,"value-changed",{value:t})}},{key:"_duplicateAction",value:function(e){e.stopPropagation();var t=e.target.index;(0,g.r)(this,"value-changed",{value:this.actions.toSpliced(t+1,0,(0,p.A)(this.actions[t]))})}},{key:"_insertAfter",value:function(e){var t;e.stopPropagation();var i=e.target.index,o=(0,f.e)(e.detail.value);this.highlightedActions=o,(0,g.r)(this,"value-changed",{value:(t=this.actions).toSpliced.apply(t,[i+1,0].concat((0,a.A)(o)))})}},{key:"_handleDragKeydown",value:function(e){"Enter"!==e.key&&" "!==e.key||(e.stopPropagation(),this._rowSortSelected=void 0===this._rowSortSelected?e.target.index:void 0)}},{key:"_stopSortSelection",value:function(){this._rowSortSelected=void 0}}]);var i,u,_,m}(v.WF);q.styles=C.Ju,(0,u.__decorate)([(0,_.MZ)({attribute:!1})],q.prototype,"hass",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],q.prototype,"narrow",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],q.prototype,"disabled",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],q.prototype,"root",void 0),(0,u.__decorate)([(0,_.MZ)({attribute:!1})],q.prototype,"actions",void 0),(0,u.__decorate)([(0,_.MZ)({attribute:!1})],q.prototype,"highlightedActions",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean,attribute:"sidebar"})],q.prototype,"optionsInSidebar",void 0),(0,u.__decorate)([(0,_.wk)()],q.prototype,"_rowSortSelected",void 0),(0,u.__decorate)([(0,_.wk)(),(0,m.I)({key:"automationClipboard",state:!0,subscribe:!0,storage:"sessionStorage"})],q.prototype,"_clipboard",void 0),(0,u.__decorate)([(0,_.YG)("ha-automation-action-row")],q.prototype,"_actionRowElements",void 0),q=(0,u.__decorate)([(0,_.EM)("ha-automation-action")],q),t()}catch(O){t(O)}}))},84648:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),o=i(50264),n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=(i(28706),i(62826)),d=i(96196),h=i(77845),u=i(55376),p=i(92542),v=i(39396),_=i(90772),y=i(3429),f=i(36857),m=i(10754),g=e([_,y,m]);[_,y,m]=g.then?(await g)():g;var b,$,A,w=e=>e,M=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e.narrow=!1,e.indent=!1,e._showDefault=!1,e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){var e=this.action,t=e.choose?(0,u.e)(e.choose):[];return(0,d.qy)(b||(b=w`
      <ha-automation-option
        .options=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .narrow=${0}
        .optionsInSidebar=${0}
        .showDefaultActions=${0}
        @show-default-actions=${0}
      ></ha-automation-option>

      ${0}
    `),t,this.disabled,this._optionsChanged,this.hass,this.narrow,this.indent,this._showDefault||!!e.default,this._addDefault,this._showDefault||e.default?(0,d.qy)($||($=w`
            <ha-automation-option-row
              .defaultActions=${0}
              .narrow=${0}
              .disabled=${0}
              .hass=${0}
              .optionsInSidebar=${0}
              @value-changed=${0}
            ></ha-automation-option-row>
          `),(0,u.e)(e.default)||[],this.narrow,this.disabled,this.hass,this.indent,this._defaultChanged):d.s6)}},{key:"_addDefault",value:(i=(0,o.A)((0,a.A)().m((function e(){var t,i;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return this._showDefault=!0,e.n=1,null===(t=this._defaultOptionRowElement)||void 0===t?void 0:t.updateComplete;case 1:null===(i=this._defaultOptionRowElement)||void 0===i||i.expand();case 2:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_optionsChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,p.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{choose:t})})}},{key:"_defaultChanged",value:function(e){e.stopPropagation(),this._showDefault=!0;var t=e.detail.value,i=Object.assign(Object.assign({},this.action),{},{default:t});0===t.length&&delete i.default,(0,p.r)(this,"value-changed",{value:i})}},{key:"expandAll",value:function(){var e,t;null===(e=this._optionElement)||void 0===e||e.expandAll(),null===(t=this._defaultOptionRowElement)||void 0===t||t.expandAll()}},{key:"collapseAll",value:function(){var e,t;null===(e=this._optionElement)||void 0===e||e.collapseAll(),null===(t=this._defaultOptionRowElement)||void 0===t||t.collapseAll()}}],[{key:"defaultConfig",get:function(){return{choose:[{conditions:[],sequence:[]}]}}},{key:"styles",get:function(){return[v.RF,f.aM,(0,d.AH)(A||(A=w`
        ha-automation-option-row {
          display: block;
          margin-top: 24px;
        }
        h3 {
          font-size: inherit;
          font-weight: inherit;
        }
      `))]}}]);var i}(d.WF);(0,c.__decorate)([(0,h.MZ)({attribute:!1})],M.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],M.prototype,"disabled",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],M.prototype,"action",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],M.prototype,"narrow",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],M.prototype,"indent",void 0),(0,c.__decorate)([(0,h.wk)()],M.prototype,"_showDefault",void 0),(0,c.__decorate)([(0,h.P)("ha-automation-option")],M.prototype,"_optionElement",void 0),(0,c.__decorate)([(0,h.P)("ha-automation-option-row")],M.prototype,"_defaultOptionRowElement",void 0),M=(0,c.__decorate)([(0,h.EM)("ha-automation-action-choose")],M),t()}catch(k){t(k)}}))},23556:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(78261),o=i(94741),n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=(i(28706),i(74423),i(62062),i(26910),i(18111),i(61701),i(26099),i(62826)),d=i(96196),h=i(77845),u=i(22786),p=i(92542),v=i(55124),_=i(25749),y=i(55676),f=(i(56565),i(69869),i(80812)),m=i(10038),g=i(10085),b=i(25756),$=i(78222),A=i(1425),w=i(14914),M=i(2502),k=i(29978),C=(i(40954),i(60345),i(56833)),V=i(86910),x=(i(73807),i(73249)),H=e([b,$,A,w,M,k,C,V,x,y]);[b,$,A,w,M,k,C,V,x,y]=H.then?(await H)():H;var S,L,Z,q,O,z=e=>e,E=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e.narrow=!1,e.inSidebar=!1,e.indent=!1,e._conditionDescriptions={},e._processedTypes=(0,u.A)(((t,i)=>{var a=Object.keys(y.D).map((e=>[e,i(`ui.panel.config.automation.editor.conditions.type.${e}.label`),e])),n=Object.keys(t).map((e=>{var t=(0,m.ob)(e),a=(0,m.YQ)(e);return[`${f.VH}${e}`,i(`component.${t}.conditions.${a}.name`)||e,e]}));return[].concat((0,o.A)(a),(0,o.A)(n)).sort(((t,i)=>(0,_.xL)(t[1],i[1],e.hass.locale.language)))})),e._getType=(0,u.A)(((e,t)=>e.condition in t?"platform":e.condition)),e._uiSupported=(0,u.A)((e=>void 0!==customElements.get(`ha-automation-condition-${e}`))),e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"hassSubscribe",value:function(){return[(0,m.bn)(this.hass,(e=>this._addConditions(e)))]}},{key:"_addConditions",value:function(e){this._conditionDescriptions=Object.assign(Object.assign({},this._conditionDescriptions),e)}},{key:"render",value:function(){var e=m.I8.includes(this.action.condition);return(0,d.qy)(S||(S=z`
      ${0}
      ${0}
    `),this.inSidebar||!this.inSidebar&&!this.indent?(0,d.qy)(L||(L=z`
            <ha-select
              fixedMenuPosition
              .label=${0}
              .disabled=${0}
              .value=${0}
              naturalMenuWidth
              @selected=${0}
              @closed=${0}
            >
              ${0}
            </ha-select>
          `),this.hass.localize("ui.panel.config.automation.editor.conditions.type_select"),this.disabled,this.action.condition in this._conditionDescriptions?`${f.VH}${this.action.condition}`:this.action.condition,this._typeChanged,v.d,this._processedTypes(this._conditionDescriptions,this.hass.localize).map((e=>{var t=(0,a.A)(e,3),i=t[0],o=t[1],n=t[2];return(0,d.qy)(Z||(Z=z`
                  <ha-list-item .value=${0} graphic="icon">
                    ${0}
                    <ha-condition-icon
                      slot="graphic"
                      .condition=${0}
                    ></ha-condition-icon>
                  </ha-list-item>
                `),i,o,n)}))):d.s6,this.indent&&e||this.inSidebar&&!e||!this.indent&&!this.inSidebar?(0,d.qy)(q||(q=z`
            <ha-automation-condition-editor
              .condition=${0}
              .description=${0}
              .disabled=${0}
              .hass=${0}
              @value-changed=${0}
              .narrow=${0}
              .uiSupported=${0}
              .indent=${0}
              action
            ></ha-automation-condition-editor>
          `),this.action,this._conditionDescriptions[this.action.condition],this.disabled,this.hass,this._conditionChanged,this.narrow,this._uiSupported(this._getType(this.action,this._conditionDescriptions)),this.indent):d.s6)}},{key:"_conditionChanged",value:function(e){e.stopPropagation(),(0,p.r)(this,"value-changed",{value:e.detail.value})}},{key:"_typeChanged",value:function(e){var t=e.target.value;if(t)if((0,f.Q)(t)){var i=(0,f.Dt)(t);i!==this.action.condition&&(0,p.r)(this,"value-changed",{value:{condition:i}})}else{var a=customElements.get(`ha-automation-condition-${t}`);t!==this.action.condition&&(0,p.r)(this,"value-changed",{value:Object.assign({},a.defaultConfig)})}}},{key:"expandAll",value:function(){var e;null===(e=this._conditionEditor)||void 0===e||e.expandAll()}},{key:"collapseAll",value:function(){var e;null===(e=this._conditionEditor)||void 0===e||e.collapseAll()}}],[{key:"defaultConfig",get:function(){return{condition:"state"}}}])}((0,g.E)(d.WF));E.styles=(0,d.AH)(O||(O=z`
    ha-select {
      margin-bottom: 24px;
    }
  `)),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"disabled",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],E.prototype,"action",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],E.prototype,"narrow",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"sidebar"})],E.prototype,"inSidebar",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"indent"})],E.prototype,"indent",void 0),(0,c.__decorate)([(0,h.wk)()],E.prototype,"_conditionDescriptions",void 0),(0,c.__decorate)([(0,h.P)("ha-automation-condition-editor")],E.prototype,"_conditionEditor",void 0),E=(0,c.__decorate)([(0,h.EM)("ha-automation-action-condition")],E),t()}catch(I){t(I)}}))},17550:function(e,t,i){var a,o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(16280),i(28706),i(62826)),c=i(96196),d=i(77845),h=i(92542),u=i(72125),p=(i(33464),i(68006)),v=e=>e,_=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"willUpdate",value:function(e){e.has("action")&&(this.action&&(0,u.r)(this.action)?(0,h.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.no_template_editor_support"))):this._timeData=(0,p.z)(this.action.delay))}},{key:"render",value:function(){return(0,c.qy)(a||(a=v`<ha-duration-input
      .label=${0}
      .disabled=${0}
      .data=${0}
      enable-millisecond
      required
      @value-changed=${0}
    ></ha-duration-input>`),this.hass.localize("ui.panel.config.automation.editor.actions.type.delay.delay"),this.disabled,this._timeData,this._valueChanged)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value;t&&(0,h.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{delay:t})})}}],[{key:"defaultConfig",get:function(){return{delay:""}}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],_.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],_.prototype,"disabled",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],_.prototype,"action",void 0),(0,l.__decorate)([(0,d.wk)()],_.prototype,"_timeData",void 0),_=(0,l.__decorate)([(0,d.EM)("ha-automation-action-delay")],_)},84915:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),o=i(50264),n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=(i(16280),i(28706),i(18111),i(7588),i(26099),i(23500),i(62826)),d=i(16527),h=i(96196),u=i(77845),p=i(22786),v=i(92542),_=(i(62100),i(60977)),y=(i(91120),i(34972)),f=i(74687),m=e([_]);_=(m.then?(await m)():m)[0];var g,b,$,A=e=>e,w=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e._extraFieldsData=(0,p.A)(((e,t)=>{var i={};return t.extra_fields.forEach((t=>{void 0!==e[t.name]&&(i[t.name]=e[t.name])})),i})),e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"shouldUpdate",value:function(e){return!e.has("action")||(!this.action.device_id||this.action.device_id in this.hass.devices||((0,v.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.panel.config.automation.editor.edit_unknown_device"))),!1))}},{key:"render",value:function(){var e,t=this._deviceId||this.action.device_id;return(0,h.qy)(g||(g=A`
      <ha-device-picker
        .value=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        label=${0}
      ></ha-device-picker>
      <ha-device-action-picker
        .value=${0}
        .deviceId=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        label=${0}
      ></ha-device-action-picker>
      ${0}
    `),t,this.disabled,this._devicePicked,this.hass,this.hass.localize("ui.panel.config.automation.editor.actions.type.device_id.label"),this.action,t,this.disabled,this._deviceActionPicked,this.hass,this.hass.localize("ui.panel.config.automation.editor.actions.type.device_id.action"),null!==(e=this._capabilities)&&void 0!==e&&null!==(e=e.extra_fields)&&void 0!==e&&e.length?(0,h.qy)(b||(b=A`
            <ha-form
              .hass=${0}
              .data=${0}
              .schema=${0}
              .disabled=${0}
              .computeLabel=${0}
              .computeHelper=${0}
              @value-changed=${0}
            ></ha-form>
          `),this.hass,this._extraFieldsData(this.action,this._capabilities),this._capabilities.extra_fields,this.disabled,(0,f.T_)(this.hass,this.action),(0,f.TH)(this.hass,this.action),this._extraFieldsChanged):"")}},{key:"firstUpdated",value:function(){this.hass.loadBackendTranslation("device_automation"),this._capabilities||this._getCapabilities(),this.action&&(this._origAction=this.action)}},{key:"updated",value:function(e){var t=e.get("action");t&&!(0,f.Po)(this._entityReg,t,this.action)&&(this._deviceId=void 0,this._getCapabilities())}},{key:"_getCapabilities",value:(i=(0,o.A)((0,a.A)().m((function e(){var t;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:if(!this.action.domain){e.n=2;break}return e.n=1,(0,f.jR)(this.hass,this.action);case 1:t=e.v,e.n=3;break;case 2:t=void 0;case 3:this._capabilities=t;case 4:return e.a(2)}}),e,this)}))),function(){return i.apply(this,arguments)})},{key:"_devicePicked",value:function(e){e.stopPropagation(),this._deviceId=e.target.value,void 0===this._deviceId&&(0,v.r)(this,"value-changed",{value:t.defaultConfig})}},{key:"_deviceActionPicked",value:function(e){e.stopPropagation();var t=e.detail.value;this._origAction&&(0,f.Po)(this._entityReg,this._origAction,t)&&(t=this._origAction),(0,v.r)(this,"value-changed",{value:t})}},{key:"_extraFieldsChanged",value:function(e){e.stopPropagation(),(0,v.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),e.detail.value)})}}],[{key:"defaultConfig",get:function(){return{device_id:"",domain:"",entity_id:""}}}]);var i}(h.WF);w.styles=(0,h.AH)($||($=A`
    ha-device-picker {
      display: block;
      margin-bottom: 24px;
    }

    ha-device-action-picker {
      display: block;
    }

    ha-form {
      display: block;
      margin-top: 24px;
    }
  `)),(0,c.__decorate)([(0,u.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,c.__decorate)([(0,u.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,c.__decorate)([(0,u.MZ)({type:Object})],w.prototype,"action",void 0),(0,c.__decorate)([(0,u.wk)()],w.prototype,"_deviceId",void 0),(0,c.__decorate)([(0,u.wk)()],w.prototype,"_capabilities",void 0),(0,c.__decorate)([(0,u.wk)(),(0,d.Fg)({context:y.ih,subscribe:!0})],w.prototype,"_entityReg",void 0),w=(0,c.__decorate)([(0,u.EM)("ha-automation-action-device_id")],w),t()}catch(M){t(M)}}))},49217:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(62826)),l=i(96196),c=i(77845),d=i(92542),h=i(82965),u=i(37029),p=(i(78740),i(23362)),v=i(7),_=e([h,u,p,v]);[h,u,p,v]=_.then?(await _)():_;var y,f,m=e=>e,g=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"updated",value:function(e){e.has("action")&&(this._actionData&&this._actionData!==this.action.event_data&&this._yamlEditor&&this._yamlEditor.setValue(this.action.event_data),this._actionData=this.action.event_data)}},{key:"render",value:function(){var e=this.action,t=e.event,i=e.event_data;return(0,l.qy)(y||(y=m`
      <ha-textfield
        .label=${0}
        .value=${0}
        .disabled=${0}
        @change=${0}
      ></ha-textfield>
      <ha-yaml-editor
        .hass=${0}
        .label=${0}
        .name=${0}
        .readOnly=${0}
        .defaultValue=${0}
        @value-changed=${0}
      ></ha-yaml-editor>
    `),this.hass.localize("ui.panel.config.automation.editor.actions.type.event.event"),t,this.disabled,this._eventChanged,this.hass,this.hass.localize("ui.panel.config.automation.editor.actions.type.event.event_data"),"event_data",this.disabled,i,this._dataChanged)}},{key:"_dataChanged",value:function(e){e.stopPropagation(),e.detail.isValid&&(this._actionData=e.detail.value,(0,v.Pb)(this,e))}},{key:"_eventChanged",value:function(e){e.stopPropagation(),(0,d.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{event:e.target.value})})}}],[{key:"defaultConfig",get:function(){return{event:"",event_data:{}}}}])}(l.WF);g.styles=(0,l.AH)(f||(f=m`
    ha-textfield {
      display: block;
    }
  `)),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],g.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],g.prototype,"action",void 0),(0,r.__decorate)([(0,c.P)("ha-yaml-editor",!0)],g.prototype,"_yamlEditor",void 0),g=(0,r.__decorate)([(0,c.EM)("ha-automation-action-event")],g),t()}catch(b){t(b)}}))},36742:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(18111),i(7588),i(26099),i(23500),i(62826)),l=i(96196),c=i(77845),d=i(92542),h=(i(78740),i(39396)),u=i(10754),p=e([u]);u=(p.then?(await p)():p)[0];var v,_,y=e=>e,f=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e.narrow=!1,e.indent=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e,t,i=this.action;return(0,l.qy)(v||(v=y`
      <h4>
        ${0}:
      </h4>
      <ha-automation-condition
        .conditions=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .narrow=${0}
        .optionsInSidebar=${0}
      ></ha-automation-condition>

      <h4>
        ${0}:
      </h4>
      <ha-automation-action
        .actions=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .narrow=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
      <h4>
        ${0}:
      </h4>
      <ha-automation-action
        .actions=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .narrow=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
    `),this.hass.localize("ui.panel.config.automation.editor.actions.type.if.if"),null!==(e=i.if)&&void 0!==e?e:[],this.disabled,this._ifChanged,this.hass,this.narrow,this.indent,this.hass.localize("ui.panel.config.automation.editor.actions.type.if.then"),null!==(t=i.then)&&void 0!==t?t:[],this.disabled,this._thenChanged,this.hass,this.narrow,this.indent,this.hass.localize("ui.panel.config.automation.editor.actions.type.if.else"),i.else||[],this.disabled,this._elseChanged,this.hass,this.narrow,this.indent)}},{key:"_ifChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,d.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{if:t})})}},{key:"_thenChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,d.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{then:t})})}},{key:"_elseChanged",value:function(e){e.stopPropagation();var t=e.detail.value,i=Object.assign(Object.assign({},this.action),{},{else:t});0===t.length&&delete i.else,(0,d.r)(this,"value-changed",{value:i})}},{key:"expandAll",value:function(){var e,t;null===(e=this._conditionElement)||void 0===e||e.expandAll(),null===(t=this._actionElements)||void 0===t||t.forEach((e=>{var t;return null===(t=e.expandAll)||void 0===t?void 0:t.call(e)}))}},{key:"collapseAll",value:function(){var e,t;null===(e=this._conditionElement)||void 0===e||e.collapseAll(),null===(t=this._actionElements)||void 0===t||t.forEach((e=>{var t;return null===(t=e.collapseAll)||void 0===t?void 0:t.call(e)}))}}],[{key:"defaultConfig",get:function(){return{if:[],then:[]}}},{key:"styles",get:function(){return[h.RF,(0,l.AH)(_||(_=y`
        h4 {
          color: var(--secondary-text-color);
          margin-bottom: 8px;
        }
        h4:first-child {
          margin-top: 0;
        }
      `))]}}])}(l.WF);(0,r.__decorate)([(0,c.MZ)({attribute:!1})],f.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],f.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],f.prototype,"action",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],f.prototype,"narrow",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],f.prototype,"indent",void 0),(0,r.__decorate)([(0,c.P)("ha-automation-condition")],f.prototype,"_conditionElement",void 0),(0,r.__decorate)([(0,c.YG)("ha-automation-action")],f.prototype,"_actionElements",void 0),f=(0,r.__decorate)([(0,c.EM)("ha-automation-action-if")],f),t()}catch(m){t(m)}}))},83230:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(62826)),l=i(96196),c=i(77845),d=i(92542),h=(i(78740),i(39396)),u=i(10754),p=e([u]);u=(p.then?(await p)():p)[0];var v,_=e=>e,y=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e.narrow=!1,e.indent=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e=this.action;return(0,l.qy)(v||(v=_`
      <ha-automation-action
        .actions=${0}
        .narrow=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
    `),e.parallel,this.narrow,this.disabled,this._actionsChanged,this.hass,this.indent)}},{key:"_actionsChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,d.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{parallel:t})})}},{key:"expandAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.expandAll()}},{key:"collapseAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.collapseAll()}}],[{key:"defaultConfig",get:function(){return{parallel:[]}}},{key:"styles",get:function(){return h.RF}}])}(l.WF);(0,r.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"narrow",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"action",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"indent",void 0),(0,r.__decorate)([(0,c.P)("ha-automation-action")],y.prototype,"_actionElement",void 0),y=(0,r.__decorate)([(0,c.EM)("ha-automation-action-parallel")],y),t()}catch(f){t(f)}}))},73118:function(e,t,i){i.a(e,(async function(e,a){try{i.d(t,{m:function(){return A}});var o=i(94741),n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=(i(28706),i(50113),i(23418),i(44114),i(18111),i(7588),i(26099),i(23500),i(62826)),d=i(96196),h=i(77845),u=i(22786),p=i(92542),v=(i(78740),i(39396)),_=i(10754),y=i(72125),f=(i(91120),e([_]));_=(f.then?(await f)():f)[0];var m,g,b=e=>e,$=["count","while","until","for_each"],A=e=>$.find((t=>t in e)),w=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),s=0;s<i;s++)a[s]=arguments[s];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e.narrow=!1,e.inSidebar=!1,e.indent=!1,e._schema=(0,u.A)(((e,t,i,a)=>[].concat((0,o.A)("count"!==e||!i&&(i||a)?[]:[{name:"count",required:!0,selector:t?{template:{}}:{number:{mode:"box",min:1}}}]),(0,o.A)("until"!==e&&"while"!==e||!a&&(i||a)?[]:[{name:e,selector:{condition:{optionsInSidebar:a}}}]),(0,o.A)("for_each"!==e||!i&&(i||a)?[]:[{name:"for_each",required:!0,selector:{object:{}}}]),(0,o.A)(a||!i&&!a?[{name:"sequence",selector:{action:{optionsInSidebar:a}}}]:[])))),e._computeLabelCallback=t=>{switch(t.name){case"count":return e.hass.localize("ui.panel.config.automation.editor.actions.type.repeat.type.count.label");case"while":return e.hass.localize("ui.panel.config.automation.editor.actions.type.repeat.type.while.conditions")+":";case"until":return e.hass.localize("ui.panel.config.automation.editor.actions.type.repeat.type.until.conditions")+":";case"for_each":return e.hass.localize("ui.panel.config.automation.editor.actions.type.repeat.type.for_each.items")+":";case"sequence":return e.hass.localize("ui.panel.config.automation.editor.actions.type.repeat.sequence")+":"}return""},e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){var e=this.action.repeat,t=A(e),i=this._schema(null!=t?t:"count","count"in e&&"string"==typeof e.count&&(0,y.F)(e.count),this.inSidebar,this.indent),a=Object.assign(Object.assign({},e),{},{type:t});return(0,d.qy)(m||(m=b`<ha-form
      .hass=${0}
      .data=${0}
      .schema=${0}
      .disabled=${0}
      @value-changed=${0}
      .computeLabel=${0}
      .narrow=${0}
    ></ha-form>`),this.hass,a,i,this.disabled,this._valueChanged,this._computeLabelCallback,this.narrow)}},{key:"_valueChanged",value:function(e){e.stopPropagation();var t=e.detail.value,i=t.type;if(delete t.type,i!==A(this.action.repeat)){var a,o;if("count"===i&&(t.count=2,delete t.while,delete t.until,delete t.for_each),"while"===i)t.while=null!==(a=t.until)&&void 0!==a?a:[],delete t.count,delete t.until,delete t.for_each;if("until"===i)t.until=null!==(o=t.while)&&void 0!==o?o:[],delete t.count,delete t.while,delete t.for_each;"for_each"===i&&(t.for_each={},delete t.count,delete t.while,delete t.until)}(0,p.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{repeat:Object.assign({},t)})})}},{key:"_getSelectorElements",value:function(){if(this._formElement){var e,t=null===(e=this._formElement.shadowRoot)||void 0===e?void 0:e.querySelectorAll("ha-selector"),i=[];return null==t||t.forEach((e=>{var t;i.push.apply(i,(0,o.A)(Array.from((null===(t=e.shadowRoot)||void 0===t?void 0:t.querySelectorAll("ha-selector-condition, ha-selector-action"))||[])))})),i}return[]}},{key:"expandAll",value:function(){this._getSelectorElements().forEach((e=>{var t;null===(t=e.expandAll)||void 0===t||t.call(e)}))}},{key:"collapseAll",value:function(){this._getSelectorElements().forEach((e=>{var t;null===(t=e.collapseAll)||void 0===t||t.call(e)}))}}],[{key:"defaultConfig",get:function(){return{repeat:{count:2,sequence:[]}}}},{key:"styles",get:function(){return[v.RF,(0,d.AH)(g||(g=b`
        ha-textfield {
          margin-top: 16px;
        }
      `))]}}])}(d.WF);(0,c.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],w.prototype,"narrow",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],w.prototype,"action",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"sidebar"})],w.prototype,"inSidebar",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean,attribute:"indent"})],w.prototype,"indent",void 0),(0,c.__decorate)([(0,h.P)("ha-form")],w.prototype,"_formElement",void 0),w=(0,c.__decorate)([(0,h.EM)("ha-automation-action-repeat")],w),a()}catch(M){a(M)}}))},14396:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(62826)),l=i(96196),c=i(77845),d=i(92542),h=(i(78740),i(39396)),u=i(10754),p=e([u]);u=(p.then?(await p)():p)[0];var v,_=e=>e,y=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e.narrow=!1,e.indent=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e=this.action;return(0,l.qy)(v||(v=_`
      <ha-automation-action
        .actions=${0}
        .narrow=${0}
        .disabled=${0}
        @value-changed=${0}
        .hass=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
    `),e.sequence,this.narrow,this.disabled,this._actionsChanged,this.hass,this.indent)}},{key:"_actionsChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,d.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{sequence:t})})}},{key:"expandAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.expandAll()}},{key:"collapseAll",value:function(){var e;null===(e=this._actionElement)||void 0===e||e.collapseAll()}}],[{key:"defaultConfig",get:function(){return{sequence:[]}}},{key:"styles",get:function(){return h.RF}}])}(l.WF);(0,r.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"narrow",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],y.prototype,"action",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],y.prototype,"indent",void 0),(0,r.__decorate)([(0,c.P)("ha-automation-action")],y.prototype,"_actionElement",void 0),y=(0,r.__decorate)([(0,c.EM)("ha-automation-action-sequence")],y),t()}catch(f){t(f)}}))},11042:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(78261),o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(16280),i(28706),i(74423),i(18111),i(13579),i(5506),i(26099),i(62826)),c=i(96196),d=i(77845),h=i(96685),u=i(92542),p=i(72125),v=i(39338),_=i(29272),y=e([v]);v=(y.then?(await y)():y)[0];var f,m,g,b,$,A=e=>e,w=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e.narrow=!1,e._responseChecked=!1,e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"willUpdate",value:function(e){if(e.has("action")){try{(0,h.vA)(this.action,_.BD)}catch(t){return void(0,u.r)(this,"ui-mode-not-available",t)}this.action&&Object.entries(this.action).some((e=>{var t=(0,a.A)(e,2),i=t[0],o=t[1];return!["data","target"].includes(i)&&(0,p.r)(o)}))?(0,u.r)(this,"ui-mode-not-available",Error(this.hass.localize("ui.errors.config.no_template_editor_support"))):this.action.entity_id?(this._action=Object.assign(Object.assign({},this.action),{},{data:Object.assign(Object.assign({},this.action.data),{},{entity_id:this.action.entity_id})}),delete this._action.entity_id):this._action=this.action}}},{key:"render",value:function(){var e,t;if(!this._action)return c.s6;var i=this._action.action?this._action.action.split(".",2):[void 0,void 0],o=(0,a.A)(i,2),n=o[0],s=o[1];return(0,c.qy)(f||(f=A`
      <ha-service-control
        .narrow=${0}
        .hass=${0}
        .value=${0}
        .disabled=${0}
        .showAdvanced=${0}
        .hidePicker=${0}
        @value-changed=${0}
      ></ha-service-control>
      ${0}
    `),this.narrow,this.hass,this._action,this.disabled,null===(e=this.hass.userData)||void 0===e?void 0:e.showAdvanced,!!this._action.metadata,this._actionChanged,n&&s&&null!==(t=this.hass.services[n])&&void 0!==t&&null!==(t=t[s])&&void 0!==t&&t.response?(0,c.qy)(m||(m=A`<ha-settings-row .narrow=${0}>
            ${0}
            <span slot="heading"
              >${0}</span
            >
            <span slot="description">
              ${0}
            </span>
            <ha-textfield
              .value=${0}
              .required=${0}
              .disabled=${0}
              @change=${0}
            ></ha-textfield>
          </ha-settings-row>`),this.narrow,this.hass.services[n][s].response.optional?(0,c.qy)(g||(g=A`<ha-checkbox
                  .checked=${0}
                  .disabled=${0}
                  @change=${0}
                  slot="prefix"
                ></ha-checkbox>`),this._action.response_variable||this._responseChecked,this.disabled,this._responseCheckboxChanged):(0,c.qy)(b||(b=A`<div slot="prefix" class="checkbox-spacer"></div>`)),this.hass.localize("ui.panel.config.automation.editor.actions.type.service.response_variable"),this.hass.services[n][s].response.optional?this.hass.localize("ui.panel.config.automation.editor.actions.type.service.has_optional_response"):this.hass.localize("ui.panel.config.automation.editor.actions.type.service.has_response"),this._action.response_variable||"",!this.hass.services[n][s].response.optional,this.disabled||this.hass.services[n][s].response.optional&&!this._action.response_variable&&!this._responseChecked,this._responseVariableChanged):c.s6)}},{key:"_actionChanged",value:function(e){e.detail.value===this._action&&e.stopPropagation();var t=Object.assign(Object.assign({},this.action),e.detail.value);if("response_variable"in this.action){var i,o=this._action.action?this._action.action.split(".",2):[void 0,void 0],n=(0,a.A)(o,2),s=n[0],r=n[1];s&&r&&null!==(i=this.hass.services[s])&&void 0!==i&&i[r]&&!("response"in this.hass.services[s][r])&&(delete t.response_variable,this._responseChecked=!1)}(0,u.r)(this,"value-changed",{value:t})}},{key:"_responseVariableChanged",value:function(e){var t=Object.assign(Object.assign({},this.action),{},{response_variable:e.target.value});e.target.value||delete t.response_variable,(0,u.r)(this,"value-changed",{value:t})}},{key:"_responseCheckboxChanged",value:function(e){if(this._responseChecked=e.target.checked,!this._responseChecked){var t=Object.assign({},this.action);delete t.response_variable,(0,u.r)(this,"value-changed",{value:t})}}}],[{key:"defaultConfig",get:function(){return{action:"",data:{}}}}])}(c.WF);w.styles=(0,c.AH)($||($=A`
    ha-service-control {
      display: block;
      margin: 0 -16px;
    }
    ha-settings-row {
      margin: 0 -16px;
      padding: var(--service-control-padding, 0 16px);
    }
    ha-settings-row {
      --settings-row-content-width: 100%;
      --settings-row-prefix-display: contents;
      border-top: var(
        --service-control-items-border-top,
        1px solid var(--divider-color)
      );
    }
    ha-checkbox {
      margin-left: -16px;
      margin-inline-start: -16px;
      margin-inline-end: initial;
    }
    .checkbox-spacer {
      width: 32px;
    }
  `)),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],w.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],w.prototype,"action",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],w.prototype,"disabled",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],w.prototype,"narrow",void 0),(0,l.__decorate)([(0,d.wk)()],w.prototype,"_action",void 0),(0,l.__decorate)([(0,d.wk)()],w.prototype,"_responseChecked",void 0),w=(0,l.__decorate)([(0,d.EM)("ha-automation-action-service")],w),t()}catch(M){t(M)}}))},47961:function(e,t,i){var a,o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(28706),i(62826)),c=i(96196),d=i(77845),h=(i(91120),e=>e),u=[{name:"set_conversation_response",selector:{template:{}}}],p=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._computeLabelCallback=()=>e.hass.localize("ui.panel.config.automation.editor.actions.type.set_conversation_response.label"),e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,c.qy)(a||(a=h`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        .disabled=${0}
        .computeLabel=${0}
      ></ha-form>
    `),this.hass,this.action,u,this.disabled,this._computeLabelCallback)}}],[{key:"defaultConfig",get:function(){return{set_conversation_response:""}}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],p.prototype,"action",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,d.EM)("ha-automation-action-set_conversation_response")],p)},11553:function(e,t,i){var a,o,n=i(44734),s=i(56038),r=i(69683),l=i(6454),c=(i(28706),i(62826)),d=i(96196),h=i(77845),u=i(92542),p=(i(78740),i(48543),i(7153),e=>e),v=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,r.A)(this,t,[].concat(a))).disabled=!1,e}return(0,l.A)(t,e),(0,s.A)(t,[{key:"render",value:function(){var e=this.action,t=e.error,i=e.stop,o=e.response_variable;return(0,d.qy)(a||(a=p`
      <ha-textfield
        .label=${0}
        .value=${0}
        .disabled=${0}
        @change=${0}
      ></ha-textfield>
      <ha-textfield
        .label=${0}
        .value=${0}
        .disabled=${0}
        @change=${0}
      ></ha-textfield>
      <ha-formfield
        .disabled=${0}
        .label=${0}
      >
        <ha-switch
          .disabled=${0}
          .checked=${0}
          @change=${0}
        ></ha-switch>
      </ha-formfield>
    `),this.hass.localize("ui.panel.config.automation.editor.actions.type.stop.stop"),i,this.disabled,this._stopChanged,this.hass.localize("ui.panel.config.automation.editor.actions.type.stop.response_variable"),o||"",this.disabled,this._responseChanged,this.disabled,this.hass.localize("ui.panel.config.automation.editor.actions.type.stop.error"),this.disabled,null!=t&&t,this._errorChanged)}},{key:"_stopChanged",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{stop:e.target.value})})}},{key:"_responseChanged",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{response_variable:e.target.value})})}},{key:"_errorChanged",value:function(e){e.stopPropagation(),(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{error:e.target.checked})})}}],[{key:"defaultConfig",get:function(){return{stop:""}}}])}(d.WF);v.styles=(0,d.AH)(o||(o=p`
    ha-textfield {
      display: block;
      margin-bottom: 24px;
    }
  `)),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"hass",void 0),(0,c.__decorate)([(0,h.MZ)({attribute:!1})],v.prototype,"action",void 0),(0,c.__decorate)([(0,h.MZ)({type:Boolean})],v.prototype,"disabled",void 0),v=(0,c.__decorate)([(0,h.EM)("ha-automation-action-stop")],v)},31267:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(44734),o=i(56038),n=i(69683),s=i(6454),r=(i(28706),i(62826)),l=i(96196),c=i(77845),d=i(55376),h=i(68006),u=i(92542),p=(i(33464),i(48543),i(78740),i(82720)),v=i(7),_=e([p,v]);[p,v]=_.then?(await _)():_;var y,f,m,g,b=e=>e,$=function(e){function t(){var e;(0,a.A)(this,t);for(var i=arguments.length,o=new Array(i),s=0;s<i;s++)o[s]=arguments[s];return(e=(0,n.A)(this,t,[].concat(o))).disabled=!1,e.narrow=!1,e.inSidebar=!1,e.indent=!1,e}return(0,s.A)(t,e),(0,o.A)(t,[{key:"render",value:function(){var e,t=(0,h.z)(this.action.timeout);return(0,l.qy)(y||(y=b`
      ${0}
      ${0}
    `),this.inSidebar||!this.inSidebar&&!this.indent?(0,l.qy)(f||(f=b`
            <ha-duration-input
              .label=${0}
              .data=${0}
              .disabled=${0}
              enable-millisecond
              @value-changed=${0}
            ></ha-duration-input>
            <ha-formfield
              .disabled=${0}
              .label=${0}
            >
              <ha-switch
                .checked=${0}
                .disabled=${0}
                @change=${0}
              ></ha-switch>
            </ha-formfield>
          `),this.hass.localize("ui.panel.config.automation.editor.actions.type.wait_for_trigger.timeout"),t,this.disabled,this._timeoutChanged,this.disabled,this.hass.localize("ui.panel.config.automation.editor.actions.type.wait_for_trigger.continue_timeout"),null===(e=this.action.continue_on_timeout)||void 0===e||e,this.disabled,this._continueChanged):l.s6,this.indent||!this.inSidebar&&!this.indent?(0,l.qy)(m||(m=b`<ha-automation-trigger
            class=${0}
            .triggers=${0}
            .hass=${0}
            .disabled=${0}
            .name=${0}
            @value-changed=${0}
            .optionsInSidebar=${0}
            .narrow=${0}
          ></ha-automation-trigger>`),this.inSidebar||this.indent?"":"expansion-panel",(0,d.e)(this.action.wait_for_trigger),this.hass,this.disabled,"wait_for_trigger",this._valueChanged,this.indent,this.narrow):l.s6)}},{key:"_timeoutChanged",value:function(e){e.stopPropagation();var t=e.detail.value;(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{timeout:t})})}},{key:"_continueChanged",value:function(e){(0,u.r)(this,"value-changed",{value:Object.assign(Object.assign({},this.action),{},{continue_on_timeout:e.target.checked})})}},{key:"_valueChanged",value:function(e){(0,v.Pb)(this,e)}}],[{key:"defaultConfig",get:function(){return{wait_for_trigger:[]}}}])}(l.WF);$.styles=(0,l.AH)(g||(g=b`
    ha-duration-input {
      display: block;
      margin-bottom: 24px;
    }
    ha-automation-trigger.expansion-panel {
      display: block;
      margin-top: 24px;
    }
  `)),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],$.prototype,"hass",void 0),(0,r.__decorate)([(0,c.MZ)({attribute:!1})],$.prototype,"action",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],$.prototype,"disabled",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean})],$.prototype,"narrow",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean,attribute:"sidebar"})],$.prototype,"inSidebar",void 0),(0,r.__decorate)([(0,c.MZ)({type:Boolean,attribute:"indent"})],$.prototype,"indent",void 0),$=(0,r.__decorate)([(0,c.EM)("ha-automation-action-wait_for_trigger")],$),t()}catch(A){t(A)}}))},2117:function(e,t,i){var a,o=i(44734),n=i(56038),s=i(69683),r=i(6454),l=(i(28706),i(62826)),c=i(96196),d=i(77845),h=(i(91120),e=>e),u=[{name:"wait_template",selector:{template:{}}},{name:"timeout",required:!1,selector:{text:{}}},{name:"continue_on_timeout",selector:{boolean:{}}}],p=function(e){function t(){var e;(0,o.A)(this,t);for(var i=arguments.length,a=new Array(i),n=0;n<i;n++)a[n]=arguments[n];return(e=(0,s.A)(this,t,[].concat(a))).disabled=!1,e._computeLabelCallback=t=>e.hass.localize(`ui.panel.config.automation.editor.actions.type.wait_template.${"continue_on_timeout"===t.name?"continue_timeout":t.name}`),e}return(0,r.A)(t,e),(0,n.A)(t,[{key:"render",value:function(){return(0,c.qy)(a||(a=h`
      <ha-form
        .hass=${0}
        .data=${0}
        .schema=${0}
        .disabled=${0}
        .computeLabel=${0}
      ></ha-form>
    `),this.hass,this.action,u,this.disabled,this._computeLabelCallback)}}],[{key:"defaultConfig",get:function(){return{wait_template:"",continue_on_timeout:!0}}}])}(c.WF);(0,l.__decorate)([(0,d.MZ)({attribute:!1})],p.prototype,"hass",void 0),(0,l.__decorate)([(0,d.MZ)({attribute:!1})],p.prototype,"action",void 0),(0,l.__decorate)([(0,d.MZ)({type:Boolean})],p.prototype,"disabled",void 0),p=(0,l.__decorate)([(0,d.EM)("ha-automation-action-wait_template")],p)},3429:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),o=i(50264),n=i(44734),s=i(56038),r=i(75864),l=i(69683),c=i(6454),d=(i(28706),i(2892),i(62826)),h=i(16527),u=i(96196),p=i(77845),v=i(94333),_=i(55376),y=i(92542),f=i(91737),m=i(55124),g=i(74522),b=(i(27639),i(95379),i(34811),i(60733),i(63419),i(99892),i(60961),i(53295)),$=i(34972),A=i(10234),w=i(98315),M=i(10754),k=i(1152),C=i(36857),V=i(4848),x=e([M,k,b]);[M,k,b]=x.then?(await x)():x;var H,S,L,Z,q,O,z,E,I,P,j,B,D,R=e=>e,F=function(e){function t(){var e;(0,n.A)(this,t);for(var i=arguments.length,s=new Array(i),c=0;c<i;c++)s[c]=arguments[c];return(e=(0,l.A)(this,t,[].concat(s))).narrow=!1,e.disabled=!1,e.first=!1,e.last=!1,e.optionsInSidebar=!1,e.sortSelected=!1,e._expanded=!1,e._selected=!1,e._collapsed=!0,e._duplicateOption=()=>{(0,y.r)((0,r.A)(e),"duplicate")},e._removeOption=()=>{e.option&&((0,y.r)((0,r.A)(e),"value-changed",{value:null}),e._selected&&(0,y.r)((0,r.A)(e),"close-sidebar"),(0,V.P)((0,r.A)(e),{message:e.hass.localize("ui.common.successfully_deleted"),duration:4e3,action:{text:e.hass.localize("ui.common.undo"),action:()=>{(0,y.r)(window,"undo-change")}}}))},e._renameOption=(0,o.A)((0,a.A)().m((function t(){var i,o;return(0,a.A)().w((function(t){for(;;)switch(t.n){case 0:return t.n=1,(0,A.an)((0,r.A)(e),{title:e.hass.localize("ui.panel.config.automation.editor.actions.type.choose.change_alias"),inputLabel:e.hass.localize("ui.panel.config.automation.editor.actions.type.choose.alias"),inputType:"string",placeholder:(0,g.Z)(e._getDescription()),defaultValue:e.option.alias,confirmText:e.hass.localize("ui.common.submit")});case 1:null!==(i=t.v)&&(o=Object.assign({},e.option),""===i?delete o.alias:o.alias=i,(0,y.r)((0,r.A)(e),"value-changed",{value:o}));case 2:return t.a(2)}}),t)}))),e}return(0,c.A)(t,e),(0,s.A)(t,[{key:"selected",get:function(){return this._selected}},{key:"_expandedChanged",value:function(e){"option"===e.currentTarget.id&&(this._expanded=e.detail.expanded)}},{key:"_getDescription",value:function(){var e=(0,_.e)(this.option.conditions);if(!e||0===e.length)return this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.no_conditions");var t="";return"string"==typeof e[0]?t+=e[0]:t+=(0,b.p)(e[0],this.hass,this._entityReg),e.length>1&&(t+=this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.option_description_additional",{numberOfAdditionalConditions:e.length-1})),t}},{key:"_renderOverflowLabel",value:function(e,t){return(0,u.qy)(H||(H=R`
      <div class="overflow-label">
        ${0}
        ${0}
      </div>
    `),e,this.optionsInSidebar&&!this.narrow?t||(0,u.qy)(S||(S=R`<span
              class="shortcut-placeholder ${0}"
            ></span>`),w.c?"mac":""):u.s6)}},{key:"_renderRow",value:function(){return(0,u.qy)(L||(L=R`
      <h3 slot="header">
        ${0}
      </h3>

      <slot name="icons" slot="icons"></slot>

      ${0}
      ${0}
    `),this.option?`${this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.option",{number:this.index+1})}: ${this.option.alias||(this._expanded?"":this._getDescription())}`:this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.default"),this.option?(0,u.qy)(Z||(Z=R`
            <ha-md-button-menu
              quick
              slot="icons"
              @click=${0}
              @closed=${0}
              @keydown=${0}
              positioning="fixed"
              anchor-corner="end-end"
              menu-corner="start-end"
            >
              <ha-icon-button
                slot="trigger"
                .label=${0}
                .path=${0}
              ></ha-icon-button>

              <ha-md-menu-item
                @click=${0}
                .disabled=${0}
              >
                <ha-svg-icon slot="start" .path=${0}></ha-svg-icon>
                ${0}
              </ha-md-menu-item>

              <ha-md-menu-item
                @click=${0}
                .disabled=${0}
              >
                <ha-svg-icon
                  slot="start"
                  .path=${0}
                ></ha-svg-icon>

                ${0}
              </ha-md-menu-item>

              ${0}

              <ha-md-menu-item
                @click=${0}
                class="warning"
                .disabled=${0}
              >
                <ha-svg-icon
                  class="warning"
                  slot="start"
                  .path=${0}
                ></ha-svg-icon>
                ${0}
              </ha-md-menu-item>
            </ha-md-button-menu>
          `),f.C,m.d,m.d,this.hass.localize("ui.common.menu"),"M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z",this._renameOption,this.disabled,"M18,17H10.5L12.5,15H18M6,17V14.5L13.88,6.65C14.07,6.45 14.39,6.45 14.59,6.65L16.35,8.41C16.55,8.61 16.55,8.92 16.35,9.12L8.47,17M19,3H5C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V5C21,3.89 20.1,3 19,3Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.triggers.rename")),this._duplicateOption,this.disabled,"M16,8H14V11H11V13H14V16H16V13H19V11H16M2,12C2,9.21 3.64,6.8 6,5.68V3.5C2.5,4.76 0,8.09 0,12C0,15.91 2.5,19.24 6,20.5V18.32C3.64,17.2 2,14.79 2,12M15,3C10.04,3 6,7.04 6,12C6,16.96 10.04,21 15,21C19.96,21 24,16.96 24,12C24,7.04 19.96,3 15,3M15,19C11.14,19 8,15.86 8,12C8,8.14 11.14,5 15,5C18.86,5 22,8.14 22,12C22,15.86 18.86,19 15,19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.duplicate")),this.optionsInSidebar?u.s6:(0,u.qy)(q||(q=R`
                    <ha-md-menu-item
                      .clickAction=${0}
                      .disabled=${0}
                    >
                      ${0}
                      <ha-svg-icon
                        slot="start"
                        .path=${0}
                      ></ha-svg-icon
                    ></ha-md-menu-item>
                    <ha-md-menu-item
                      .clickAction=${0}
                      .disabled=${0}
                    >
                      ${0}
                      <ha-svg-icon
                        slot="start"
                        .path=${0}
                      ></ha-svg-icon
                    ></ha-md-menu-item>
                  `),this._moveUp,this.disabled||!!this.first,this.hass.localize("ui.panel.config.automation.editor.move_up"),"M13,20H11V8L5.5,13.5L4.08,12.08L12,4.16L19.92,12.08L18.5,13.5L13,8V20Z",this._moveDown,this.disabled||!!this.last,this.hass.localize("ui.panel.config.automation.editor.move_down"),"M11,4H13V16L18.5,10.5L19.92,11.92L12,19.84L4.08,11.92L5.5,10.5L11,16V4Z"),this._removeOption,this.disabled,"M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z",this._renderOverflowLabel(this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.remove_option"),(0,u.qy)(O||(O=R`<span class="shortcut">
                    <span
                      >${0}</span
                    >
                    <span>+</span>
                    <span
                      >${0}</span
                    >
                  </span>`),w.c?(0,u.qy)(z||(z=R`<ha-svg-icon
                            slot="start"
                            .path=${0}
                          ></ha-svg-icon>`),"M6,2A4,4 0 0,1 10,6V8H14V6A4,4 0 0,1 18,2A4,4 0 0,1 22,6A4,4 0 0,1 18,10H16V14H18A4,4 0 0,1 22,18A4,4 0 0,1 18,22A4,4 0 0,1 14,18V16H10V18A4,4 0 0,1 6,22A4,4 0 0,1 2,18A4,4 0 0,1 6,14H8V10H6A4,4 0 0,1 2,6A4,4 0 0,1 6,2M16,18A2,2 0 0,0 18,20A2,2 0 0,0 20,18A2,2 0 0,0 18,16H16V18M14,10H10V14H14V10M6,16A2,2 0 0,0 4,18A2,2 0 0,0 6,20A2,2 0 0,0 8,18V16H6M8,6A2,2 0 0,0 6,4A2,2 0 0,0 4,6A2,2 0 0,0 6,8H8V6M18,8A2,2 0 0,0 20,6A2,2 0 0,0 18,4A2,2 0 0,0 16,6V8H18Z"):this.hass.localize("ui.panel.config.automation.editor.ctrl"),this.hass.localize("ui.panel.config.automation.editor.del")))):u.s6,this.optionsInSidebar?u.s6:this._renderContent())}},{key:"_renderContent",value:function(){return(0,u.qy)(E||(E=R`<div
      class=${0}
    >
      ${0}
      <h4 class=${0}>
        ${0}:
      </h4>
      <ha-automation-action
        .actions=${0}
        .disabled=${0}
        .hass=${0}
        .narrow=${0}
        @value-changed=${0}
        .optionsInSidebar=${0}
      ></ha-automation-action>
    </div>`),(0,v.H)({"card-content":!0,card:!this.optionsInSidebar,indent:this.optionsInSidebar,selected:this._selected,hidden:this.optionsInSidebar&&this._collapsed}),this.option?(0,u.qy)(I||(I=R`
            <h4 class="top">
              ${0}:
            </h4>
            <ha-automation-condition
              .conditions=${0}
              .disabled=${0}
              .hass=${0}
              .narrow=${0}
              @value-changed=${0}
              .optionsInSidebar=${0}
            ></ha-automation-condition>
          `),this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.conditions"),(0,_.e)(this.option.conditions),this.disabled,this.hass,this.narrow,this._conditionChanged,this.optionsInSidebar):u.s6,this.option?"":"top",this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.sequence"),this.option?(0,_.e)(this.option.sequence)||[]:this.defaultActions&&(0,_.e)(this.defaultActions)||[],this.disabled,this.hass,this.narrow,this._actionChanged,this.optionsInSidebar)}},{key:"render",value:function(){return this.option||this.defaultActions?(0,u.qy)(P||(P=R`
      <ha-card outlined class=${0}>
        ${0}
      </ha-card>

      ${0}
    `),this._selected?"selected":"",this.optionsInSidebar?(0,u.qy)(j||(j=R`<ha-automation-row
              left-chevron
              .collapsed=${0}
              .selected=${0}
              .sortSelected=${0}
              @click=${0}
              @toggle-collapsed=${0}
              @delete-row=${0}
              >${0}</ha-automation-row
            >`),this._collapsed,this._selected,this.sortSelected,this._toggleSidebar,this._toggleCollapse,this._removeOption,this._renderRow()):(0,u.qy)(B||(B=R`
              <ha-expansion-panel
                left-chevron
                @expanded-changed=${0}
                id="option"
              >
                ${0}
              </ha-expansion-panel>
            `),this._expandedChanged,this._renderRow()),this.optionsInSidebar?this._renderContent():u.s6):u.s6}},{key:"_moveUp",value:function(){(0,y.r)(this,"move-up")}},{key:"_moveDown",value:function(){(0,y.r)(this,"move-down")}},{key:"_conditionChanged",value:function(e){e.stopPropagation();var t=e.detail.value,i=Object.assign(Object.assign({},this.option),{},{conditions:t});(0,y.r)(this,"value-changed",{value:i})}},{key:"_actionChanged",value:function(e){if(!this.defaultActions){e.stopPropagation();var t=e.detail.value,i=Object.assign(Object.assign({},this.option),{},{sequence:t});(0,y.r)(this,"value-changed",{value:i})}}},{key:"_toggleSidebar",value:function(e){null==e||e.stopPropagation(),this._selected?(0,y.r)(this,"request-close-sidebar"):this.openSidebar()}},{key:"openSidebar",value:function(){(0,y.r)(this,"open-sidebar",{close:e=>{this._selected=!1,(0,y.r)(this,"close-sidebar"),e&&this.focus()},rename:()=>{this._renameOption()},delete:this._removeOption,duplicate:this._duplicateOption,defaultOption:!!this.defaultActions}),this._selected=!0,this._collapsed=!1,this.narrow&&window.setTimeout((()=>{this.scrollIntoView({block:"start",behavior:"smooth"})}),180)}},{key:"expand",value:function(){this.optionsInSidebar?this._collapsed=!1:this.updateComplete.then((()=>{this.shadowRoot.querySelector("ha-expansion-panel").expanded=!0}))}},{key:"collapse",value:function(){this._collapsed=!0}},{key:"expandAll",value:function(){var e,t;this.expand(),null===(e=this._conditionElement)||void 0===e||e.expandAll(),null===(t=this._actionElement)||void 0===t||t.expandAll()}},{key:"collapseAll",value:function(){var e,t;this.collapse(),null===(e=this._conditionElement)||void 0===e||e.collapseAll(),null===(t=this._actionElement)||void 0===t||t.collapseAll()}},{key:"_toggleCollapse",value:function(){this._collapsed=!this._collapsed}},{key:"focus",value:function(){var e;null===(e=this._automationRowElement)||void 0===e||e.focus()}}],[{key:"styles",get:function(){return[C.bH,C.yj,C.Lt,C.aM,(0,u.AH)(D||(D=R`
        li[role="separator"] {
          border-bottom-color: var(--divider-color);
        }
        h4 {
          color: var(--ha-color-text-secondary);
        }
        h4 {
          margin-bottom: 8px;
        }
        h4.top {
          margin-top: 0;
        }
      `))]}}])}(u.WF);(0,d.__decorate)([(0,p.MZ)({attribute:!1})],F.prototype,"hass",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],F.prototype,"option",void 0),(0,d.__decorate)([(0,p.MZ)({attribute:!1})],F.prototype,"defaultActions",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],F.prototype,"narrow",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],F.prototype,"disabled",void 0),(0,d.__decorate)([(0,p.MZ)({type:Number})],F.prototype,"index",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],F.prototype,"first",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean})],F.prototype,"last",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean,attribute:"sidebar"})],F.prototype,"optionsInSidebar",void 0),(0,d.__decorate)([(0,p.MZ)({type:Boolean,attribute:"sort-selected"})],F.prototype,"sortSelected",void 0),(0,d.__decorate)([(0,p.wk)()],F.prototype,"_expanded",void 0),(0,d.__decorate)([(0,p.wk)()],F.prototype,"_selected",void 0),(0,d.__decorate)([(0,p.wk)()],F.prototype,"_collapsed",void 0),(0,d.__decorate)([(0,p.wk)(),(0,h.Fg)({context:$.ih,subscribe:!0})],F.prototype,"_entityReg",void 0),(0,d.__decorate)([(0,p.P)("ha-automation-condition")],F.prototype,"_conditionElement",void 0),(0,d.__decorate)([(0,p.P)("ha-automation-action")],F.prototype,"_actionElement",void 0),(0,d.__decorate)([(0,p.P)("ha-automation-row")],F.prototype,"_automationRowElement",void 0),F=(0,d.__decorate)([(0,p.EM)("ha-automation-option-row")],F),t()}catch(N){t(N)}}))},90772:function(e,t,i){i.a(e,(async function(e,t){try{var a=i(61397),o=i(94741),n=i(50264),s=i(44734),r=i(56038),l=i(75864),c=i(69683),d=i(6454),h=i(25460),u=(i(28706),i(2008),i(23792),i(34782),i(54554),i(71658),i(18111),i(22489),i(7588),i(26099),i(38781),i(73772),i(23500),i(62953),i(62826)),p=i(34271),v=i(96196),_=i(77845),y=i(4937),f=i(42256),m=i(92542),g=i(55124),b=i(99034),$=i(89473),A=(i(63801),i(60961),i(36857)),w=i(3429),M=e([$,w]);[$,w]=M.then?(await M)():M;var k,C,V,x,H,S=e=>e,L="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z",Z=function(e){function t(){var e;(0,s.A)(this,t);for(var i=arguments.length,a=new Array(i),o=0;o<i;o++)a[o]=arguments[o];return(e=(0,c.A)(this,t,[].concat(a))).narrow=!1,e.disabled=!1,e.optionsInSidebar=!1,e.showDefaultActions=!1,e._focusLastOptionOnChange=!1,e._optionsKeys=new WeakMap,e._addOption=()=>{var t=e.options.concat({conditions:[],sequence:[]});e._focusLastOptionOnChange=!0,(0,m.r)((0,l.A)(e),"value-changed",{value:t})},e._showDefaultActions=()=>{(0,m.r)((0,l.A)(e),"show-default-actions")},e}return(0,d.A)(t,e),(0,r.A)(t,[{key:"render",value:function(){return(0,v.qy)(k||(k=S`
      <ha-sortable
        handle-selector=".handle"
        draggable-selector="ha-automation-option-row"
        .disabled=${0}
        group="options"
        invert-swap
        @item-moved=${0}
        @item-added=${0}
        @item-removed=${0}
      >
        <div class="rows ${0}">
          ${0}
          <div class="buttons">
            <ha-button
              appearance="filled"
              size="small"
              .disabled=${0}
              @click=${0}
            >
              <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
              ${0}
            </ha-button>
            ${0}
          </div>
        </div>
      </ha-sortable>
    `),this.disabled,this._optionMoved,this._optionAdded,this._optionRemoved,this.optionsInSidebar?"":"no-sidebar",(0,y.u)(this.options,(e=>this._getKey(e)),((e,t)=>(0,v.qy)(C||(C=S`
              <ha-automation-option-row
                .sortableData=${0}
                .index=${0}
                .first=${0}
                .last=${0}
                .option=${0}
                .narrow=${0}
                .disabled=${0}
                @duplicate=${0}
                @move-down=${0}
                @move-up=${0}
                @value-changed=${0}
                .hass=${0}
                .optionsInSidebar=${0}
                .sortSelected=${0}
                @stop-sort-selection=${0}
              >
                ${0}
              </ha-automation-option-row>
            `),e,t,0===t,t===this.options.length-1,e,this.narrow,this.disabled,this._duplicateOption,this._moveDown,this._moveUp,this._optionChanged,this.hass,this.optionsInSidebar,this._rowSortSelected===t,this._stopSortSelection,this.disabled?v.s6:(0,v.qy)(V||(V=S`
                      <div
                        tabindex="0"
                        class="handle ${0}"
                        slot="icons"
                        @keydown=${0}
                        @click=${0}
                        .index=${0}
                      >
                        <ha-svg-icon
                          .path=${0}
                        ></ha-svg-icon>
                      </div>
                    `),this._rowSortSelected===t?"active":"",this._handleDragKeydown,g.d,t,"M21 11H3V9H21V11M21 13H3V15H21V13Z")))),this.disabled,this._addOption,L,this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.add_option"),this.showDefaultActions?v.s6:(0,v.qy)(x||(x=S`<ha-button
                  appearance="plain"
                  size="small"
                  .disabled=${0}
                  @click=${0}
                >
                  <ha-svg-icon .path=${0} slot="start"></ha-svg-icon>
                  ${0}
                </ha-button>`),this.disabled,this._showDefaultActions,L,this.hass.localize("ui.panel.config.automation.editor.actions.type.choose.add_default")))}},{key:"updated",value:function(e){if((0,h.A)(t,"updated",this,3)([e]),e.has("options")&&(this._focusLastOptionOnChange||void 0!==this._focusOptionIndexOnChange)){var i=this._focusLastOptionOnChange?"new":"moved",a=this.shadowRoot.querySelector("ha-automation-option-row:"+("new"===i?"last-of-type":`nth-of-type(${this._focusOptionIndexOnChange+1})`));this._focusLastOptionOnChange=!1,this._focusOptionIndexOnChange=void 0,a.updateComplete.then((()=>{this.narrow&&a.scrollIntoView({block:"start",behavior:"smooth"}),"new"===i&&a.expand(),this.optionsInSidebar?a.openSidebar():a.focus()}))}}},{key:"expandAll",value:function(){var e;null===(e=this._optionRowElements)||void 0===e||e.forEach((e=>e.expandAll()))}},{key:"collapseAll",value:function(){var e;null===(e=this._optionRowElements)||void 0===e||e.forEach((e=>e.collapseAll()))}},{key:"_getKey",value:function(e){return this._optionsKeys.has(e)||this._optionsKeys.set(e,Math.random().toString()),this._optionsKeys.get(e)}},{key:"_moveUp",value:function(e){e.stopPropagation();var t=e.target.index;if(!e.target.first){var i=t-1;this._move(t,i),this._rowSortSelected===t&&(this._rowSortSelected=i),e.target.focus()}}},{key:"_moveDown",value:function(e){e.stopPropagation();var t=e.target.index;if(!e.target.last){var i=t+1;this._move(t,i),this._rowSortSelected===t&&(this._rowSortSelected=i),e.target.focus()}}},{key:"_move",value:function(e,t){var i=this.options.concat(),a=i.splice(e,1)[0];i.splice(t,0,a),this.options=i,(0,m.r)(this,"value-changed",{value:i})}},{key:"_optionMoved",value:function(e){e.stopPropagation();var t=e.detail,i=t.oldIndex,a=t.newIndex;this._move(i,a)}},{key:"_optionAdded",value:(u=(0,n.A)((0,a.A)().m((function e(t){var i,n,s,r,l,c;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail,n=i.index,s=i.data,r=t.detail.item,l=r.selected,c=[].concat((0,o.A)(this.options.slice(0,n)),[s],(0,o.A)(this.options.slice(n))),this.options=c,l&&(this._focusOptionIndexOnChange=1===c.length?0:n),e.n=1,(0,b.E)();case 1:(0,m.r)(this,"value-changed",{value:this.options});case 2:return e.a(2)}}),e,this)}))),function(e){return u.apply(this,arguments)})},{key:"_optionRemoved",value:(i=(0,n.A)((0,a.A)().m((function e(t){var i,o,n;return(0,a.A)().w((function(e){for(;;)switch(e.n){case 0:return t.stopPropagation(),i=t.detail.index,o=this.options[i],this.options=this.options.filter((e=>e!==o)),e.n=1,(0,b.E)();case 1:n=this.options.filter((e=>e!==o)),(0,m.r)(this,"value-changed",{value:n});case 2:return e.a(2)}}),e,this)}))),function(e){return i.apply(this,arguments)})},{key:"_optionChanged",value:function(e){e.stopPropagation();var t=(0,o.A)(this.options),i=e.detail.value,a=e.target.index;if(null===i)t.splice(a,1);else{var n=this._getKey(t[a]);this._optionsKeys.set(i,n),t[a]=i}(0,m.r)(this,"value-changed",{value:t})}},{key:"_duplicateOption",value:function(e){e.stopPropagation();var t=e.target.index;(0,m.r)(this,"value-changed",{value:this.options.toSpliced(t+1,0,(0,p.A)(this.options[t]))})}},{key:"_handleDragKeydown",value:function(e){"Enter"!==e.key&&" "!==e.key||(e.stopPropagation(),this._rowSortSelected=void 0===this._rowSortSelected?e.target.index:void 0)}},{key:"_stopSortSelection",value:function(){this._rowSortSelected=void 0}}]);var i,u}(v.WF);Z.styles=[A.Ju,(0,v.AH)(H||(H=S`
      :host([root]) .rows {
        padding-inline-end: 8px;
      }
    `))],(0,u.__decorate)([(0,_.MZ)({attribute:!1})],Z.prototype,"hass",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],Z.prototype,"narrow",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean})],Z.prototype,"disabled",void 0),(0,u.__decorate)([(0,_.MZ)({attribute:!1})],Z.prototype,"options",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean,attribute:"sidebar"})],Z.prototype,"optionsInSidebar",void 0),(0,u.__decorate)([(0,_.MZ)({type:Boolean,attribute:"show-default"})],Z.prototype,"showDefaultActions",void 0),(0,u.__decorate)([(0,_.wk)()],Z.prototype,"_rowSortSelected",void 0),(0,u.__decorate)([(0,_.wk)(),(0,f.I)({key:"automationClipboard",state:!0,subscribe:!0,storage:"sessionStorage"})],Z.prototype,"_clipboard",void 0),(0,u.__decorate)([(0,_.YG)("ha-automation-option-row")],Z.prototype,"_optionRowElements",void 0),Z=(0,u.__decorate)([(0,_.EM)("ha-automation-option")],Z),t()}catch(q){t(q)}}))}}]);
//# sourceMappingURL=5600.2f3efb4818ad2ff4.js.map