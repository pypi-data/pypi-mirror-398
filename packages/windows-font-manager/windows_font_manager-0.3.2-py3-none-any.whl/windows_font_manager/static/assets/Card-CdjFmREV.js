import{M as n,L as f,ar as J,as as Q,b1 as Z,a0 as s,N as a,d as ee,q as i,a3 as b,T as oe,U as S,a6 as re,m as y,X as z,a9 as te,Y as ne,aq as ae,bN as de,bO as g,av as se}from"./index-BXlMPVIj.js";import{N as ie}from"./Close-CCT4LwE4.js";const le=n([f("card",`
 font-size: var(--n-font-size);
 line-height: var(--n-line-height);
 display: flex;
 flex-direction: column;
 width: 100%;
 box-sizing: border-box;
 position: relative;
 border-radius: var(--n-border-radius);
 background-color: var(--n-color);
 color: var(--n-text-color);
 word-break: break-word;
 transition: 
 color .3s var(--n-bezier),
 background-color .3s var(--n-bezier),
 box-shadow .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 `,[Z({background:"var(--n-color-modal)"}),s("hoverable",[n("&:hover","box-shadow: var(--n-box-shadow);")]),s("content-segmented",[n(">",[a("content",{paddingTop:"var(--n-padding-bottom)"})])]),s("content-soft-segmented",[n(">",[a("content",`
 margin: 0 var(--n-padding-left);
 padding: var(--n-padding-bottom) 0;
 `)])]),s("footer-segmented",[n(">",[a("footer",{paddingTop:"var(--n-padding-bottom)"})])]),s("footer-soft-segmented",[n(">",[a("footer",`
 padding: var(--n-padding-bottom) 0;
 margin: 0 var(--n-padding-left);
 `)])]),n(">",[f("card-header",`
 box-sizing: border-box;
 display: flex;
 align-items: center;
 font-size: var(--n-title-font-size);
 padding:
 var(--n-padding-top)
 var(--n-padding-left)
 var(--n-padding-bottom)
 var(--n-padding-left);
 `,[a("main",`
 font-weight: var(--n-title-font-weight);
 transition: color .3s var(--n-bezier);
 flex: 1;
 min-width: 0;
 color: var(--n-title-text-color);
 `),a("extra",`
 display: flex;
 align-items: center;
 font-size: var(--n-font-size);
 font-weight: 400;
 transition: color .3s var(--n-bezier);
 color: var(--n-text-color);
 `),a("close",`
 margin: 0 0 0 8px;
 transition:
 background-color .3s var(--n-bezier),
 color .3s var(--n-bezier);
 `)]),a("action",`
 box-sizing: border-box;
 transition:
 background-color .3s var(--n-bezier),
 border-color .3s var(--n-bezier);
 background-clip: padding-box;
 background-color: var(--n-action-color);
 `),a("content","flex: 1; min-width: 0;"),a("content, footer",`
 box-sizing: border-box;
 padding: 0 var(--n-padding-left) var(--n-padding-bottom) var(--n-padding-left);
 font-size: var(--n-font-size);
 `,[n("&:first-child",{paddingTop:"var(--n-padding-bottom)"})]),a("action",`
 background-color: var(--n-action-color);
 padding: var(--n-padding-bottom) var(--n-padding-left);
 border-bottom-left-radius: var(--n-border-radius);
 border-bottom-right-radius: var(--n-border-radius);
 `)]),f("card-cover",`
 overflow: hidden;
 width: 100%;
 border-radius: var(--n-border-radius) var(--n-border-radius) 0 0;
 `,[n("img",`
 display: block;
 width: 100%;
 `)]),s("bordered",`
 border: 1px solid var(--n-border-color);
 `,[n("&:target","border-color: var(--n-color-target);")]),s("action-segmented",[n(">",[a("action",[n("&:not(:first-child)",{borderTop:"1px solid var(--n-border-color)"})])])]),s("content-segmented, content-soft-segmented",[n(">",[a("content",{transition:"border-color 0.3s var(--n-bezier)"},[n("&:not(:first-child)",{borderTop:"1px solid var(--n-border-color)"})])])]),s("footer-segmented, footer-soft-segmented",[n(">",[a("footer",{transition:"border-color 0.3s var(--n-bezier)"},[n("&:not(:first-child)",{borderTop:"1px solid var(--n-border-color)"})])])]),s("embedded",`
 background-color: var(--n-color-embedded);
 `)]),J(f("card",`
 background: var(--n-color-modal);
 `,[s("embedded",`
 background-color: var(--n-color-embedded-modal);
 `)])),Q(f("card",`
 background: var(--n-color-popover);
 `,[s("embedded",`
 background-color: var(--n-color-embedded-popover);
 `)]))]),k={title:[String,Function],contentClass:String,contentStyle:[Object,String],headerClass:String,headerStyle:[Object,String],headerExtraClass:String,headerExtraStyle:[Object,String],footerClass:String,footerStyle:[Object,String],embedded:Boolean,segmented:{type:[Boolean,Object],default:!1},size:{type:String,default:"medium"},bordered:{type:Boolean,default:!0},closable:Boolean,hoverable:Boolean,role:String,onClose:[Function,Array],tag:{type:String,default:"div"},cover:Function,content:[String,Function],footer:Function,action:Function,headerExtra:Function,closeFocusable:Boolean},fe=se(k),ce=Object.assign(Object.assign({},S.props),k),he=ee({name:"Card",props:ce,slots:Object,setup(o){const p=()=>{const{onClose:t}=o;t&&ae(t)},{inlineThemeDisabled:h,mergedClsPrefixRef:e,mergedRtlRef:u}=oe(o),c=S("Card","-card",le,de,o,e),x=re("Card",u,e),v=y(()=>{const{size:t}=o,{self:{color:r,colorModal:l,colorTarget:C,textColor:m,titleTextColor:$,titleFontWeight:w,borderColor:E,actionColor:T,borderRadius:B,lineHeight:F,closeIconColor:P,closeIconColorHover:R,closeIconColorPressed:_,closeColorHover:O,closeColorPressed:j,closeBorderRadius:M,closeIconSize:N,closeSize:I,boxShadow:V,colorPopover:H,colorEmbedded:L,colorEmbeddedModal:q,colorEmbeddedPopover:K,[z("padding",t)]:W,[z("fontSize",t)]:A,[z("titleFontSize",t)]:D},common:{cubicBezierEaseInOut:U}}=c.value,{top:X,left:Y,bottom:G}=te(W);return{"--n-bezier":U,"--n-border-radius":B,"--n-color":r,"--n-color-modal":l,"--n-color-popover":H,"--n-color-embedded":L,"--n-color-embedded-modal":q,"--n-color-embedded-popover":K,"--n-color-target":C,"--n-text-color":m,"--n-line-height":F,"--n-action-color":T,"--n-title-text-color":$,"--n-title-font-weight":w,"--n-close-icon-color":P,"--n-close-icon-color-hover":R,"--n-close-icon-color-pressed":_,"--n-close-color-hover":O,"--n-close-color-pressed":j,"--n-border-color":E,"--n-box-shadow":V,"--n-padding-top":X,"--n-padding-bottom":G,"--n-padding-left":Y,"--n-font-size":A,"--n-title-font-size":D,"--n-close-size":I,"--n-close-icon-size":N,"--n-close-border-radius":M}}),d=h?ne("card",y(()=>o.size[0]),v,o):void 0;return{rtlEnabled:x,mergedClsPrefix:e,mergedTheme:c,handleCloseClick:p,cssVars:h?void 0:v,themeClass:d?.themeClass,onRender:d?.onRender}},render(){const{segmented:o,bordered:p,hoverable:h,mergedClsPrefix:e,rtlEnabled:u,onRender:c,embedded:x,tag:v,$slots:d}=this;return c?.(),i(v,{class:[`${e}-card`,this.themeClass,x&&`${e}-card--embedded`,{[`${e}-card--rtl`]:u,[`${e}-card--content${typeof o!="boolean"&&o.content==="soft"?"-soft":""}-segmented`]:o===!0||o!==!1&&o.content,[`${e}-card--footer${typeof o!="boolean"&&o.footer==="soft"?"-soft":""}-segmented`]:o===!0||o!==!1&&o.footer,[`${e}-card--action-segmented`]:o===!0||o!==!1&&o.action,[`${e}-card--bordered`]:p,[`${e}-card--hoverable`]:h}],style:this.cssVars,role:this.role},b(d.cover,t=>{const r=this.cover?g([this.cover()]):t;return r&&i("div",{class:`${e}-card-cover`,role:"none"},r)}),b(d.header,t=>{const{title:r}=this,l=r?g(typeof r=="function"?[r()]:[r]):t;return l||this.closable?i("div",{class:[`${e}-card-header`,this.headerClass],style:this.headerStyle,role:"heading"},i("div",{class:`${e}-card-header__main`,role:"heading"},l),b(d["header-extra"],C=>{const m=this.headerExtra?g([this.headerExtra()]):C;return m&&i("div",{class:[`${e}-card-header__extra`,this.headerExtraClass],style:this.headerExtraStyle},m)}),this.closable&&i(ie,{clsPrefix:e,class:`${e}-card-header__close`,onClick:this.handleCloseClick,focusable:this.closeFocusable,absolute:!0})):null}),b(d.default,t=>{const{content:r}=this,l=r?g(typeof r=="function"?[r()]:[r]):t;return l&&i("div",{class:[`${e}-card__content`,this.contentClass],style:this.contentStyle,role:"none"},l)}),b(d.footer,t=>{const r=this.footer?g([this.footer()]):t;return r&&i("div",{class:[`${e}-card__footer`,this.footerClass],style:this.footerStyle,role:"none"},r)}),b(d.action,t=>{const r=this.action?g([this.action()]):t;return r&&i("div",{class:`${e}-card__action`,role:"none"},r)}))}});export{he as N,fe as a,k as c};
