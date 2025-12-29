<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:jp="http://www.jpo.go.jp">

    <!-- this xslt was created with reference to pat_common.xsl
         of Internet Application Software version i5.30 provided by JPO -->


    <!-- ====================================================================
            書類識別コード変換
            INPUT: code e.g. A151
            OUTPUT: 書類名 e.g. 手続補正書（方式）
         ====================================================================-->
    <xsl:template name="convert-document-code">
        <xsl:param name="code" as="xs:string" />
        <xsl:value-of
            select="key('doc-code-table-key', $code, $doc-code-table)/@value" />
    </xsl:template>

    <xsl:key name="doc-code-table-key" match="item" use="@code" />
    <xsl:variable name="doc-code-table">
        <!-- 特許 出願系 -->
        <item code="A151" value="手続補正書（方式）" />
        <item code="A1521" value="手続補正書" />
        <item code="A1522" value="手続補正書" />
        <item code="A1523" value="手続補正書" />
        <item code="A15210" value="特許協力条約第３４条補正の翻訳文提出書（職権）" />
        <item code="A15211" value="特許協力条約第３４条補正の写し提出書" />
        <item code="A15212" value="特許協力条約第３４条補正の写し提出書（職権）" />
        <item code="A1524" value="誤訳訂正書" />
        <item code="A1525" value="特許協力条約第１９条補正の翻訳文提出書" />
        <item code="A1526" value="特許協力条約第１９条補正の翻訳文提出書（職権）" />
        <item code="A1527" value="特許協力条約第１９条補正の写し提出書" />
        <item code="A1528" value="特許協力条約第１９条補正の写し提出書（職権）" />
        <item code="A1529" value="特許協力条約第３４条補正の翻訳文提出書" />
        <item code="A153" value="意見書" />
        <item code="A155" value="受継申立書" />
        <item code="A159" value="弁明書" />
        <item code="A1601" value="期間延長請求書" />
        <item code="A1621" value="出願審査請求書" />
        <item code="A1625" value="出願審査請求書（他人）" />
        <item code="A1627" value="出願公開請求書" />
        <item code="A163" value="特許願" />
        <item code="A1631" value="翻訳文提出書" />
        <item code="A1632" value="国内書面" />
        <item code="A1634" value="国際出願翻訳文提出書" />
        <item code="A1635" value="国際出願翻訳文提出書（職権）" />
        <item code="A167" value="受託番号変更届" />
        <item code="A1681" value="代表者選定届" />
        <item code="A1691" value="雑書類" />
        <item code="A1711" value="出願人名義変更届" />
        <item code="A1712" value="出願人名義変更届（一般承継）" />
        <item code="A17421" value="代理人変更届" />
        <item code="A17422" value="代理人受任届" />
        <item code="A17423" value="代理人選任届" />
        <item code="A17424" value="代理人辞任届" />
        <item code="A17425" value="代理人解任届" />
        <item code="A17426" value="代理権変更届" />
        <item code="A17427" value="代理権消滅届" />
        <item code="A17428" value="包括委任状援用制限届" />
        <item code="A17431" value="復代理人変更届" />
        <item code="A17432" value="復代理人受任届" />
        <item code="A17433" value="復代理人選任届" />
        <item code="A17434" value="復代理人辞任届" />
        <item code="A17435" value="復代理人解任届" />
        <item code="A17436" value="復代理権変更届" />
        <item code="A17437" value="復代理権消滅届" />
        <item code="A1761" value="出願取下書" />
        <item code="A1762" value="出願放棄書" />
        <item code="A1764" value="先の出願に基づく優先権主張取下書" />
        <item code="A1765" value="パリ条約による優先権主張放棄書" />
        <item code="A1781" value="上申書" />
        <item code="A179" value="優先権証明書提出書" />
        <item code="A180" value="新規性の喪失の例外証明書提出書" />
        <item code="A1801" value="新規性喪失の例外適用申請書" />
        <item code="A181" value="出願日証明書提出書" />
        <item code="A182" value="物件提出書" />
        <item code="A1821" value="手続補足書" />
        <item code="A1822" value="証明書類提出書" />
        <item code="A1831" value="刊行物等提出書" />
        <item code="A187" value="優先審査に関する事情説明書" />
        <item code="A1871" value="早期審査に関する事情説明書" />
        <item code="A1872" value="早期審査に関する事情説明補充書" />
        <item code="A1IB101" value="国際出願の写し" />
        <item code="A1IB101J" value="国際出願の願書の写し" />
        <item code="A1IB210" value="国際調査報告" />
        <item code="A1IB21J" value="国際調査報告（日本語）" />
        <item code="A1IB304" value="優先権主張の書類提出に関する通知" />
        <item code="A1IB305" value="先の出願番号の遅れた提出の通知" />
        <item code="A1IB306" value="記録の変更通知" />
        <item code="A1IB307" value="国際出願又は指定の取り下げの通知" />
        <item code="A1IB310" value="送達書類に関する通知（その他雑通知等）" />
        <item code="A1IB317" value="優先権に関する取下の通知" />
        <item code="A1IB31A" value="優先権書類" />
        <item code="A1IB31B" value="条約１９条補正" />
        <item code="A1IB31B1" value="条約１９条補正（職権）" />
        <item code="A1IB31C" value="条約３４条補正" />
        <item code="A1IB31C1" value="条約３４条補正（職権）" />
        <item code="A1IB31E" value="国際予備審査報告（日本語／英語以外の言語）" />
        <item code="A1IB31J" value="国際予備審査報告（日本語）" />
        <item code="A1IB324" value="指定が取り下げられたものとみなす旨の通知" />
        <item code="A1IB325" value="国際出願が取り下げられたものとみなす通知" />
        <item code="A1IB331" value="選択の通知" />
        <item code="A1IB334" value="後にする選択の届出が提出・選択無とみなす通知" />
        <item code="A1IB338" value="国際予備審査報告（英語）" />
        <item code="A1IB339" value="予備審査請求又は選択の取り下げの通知" />
        <item code="A1IB345" value="他に使用すべき様式がない場合の通知" />
        <item code="A1IB349" value="国際公開" />
        <item code="A1IB3491" value="日本語国際公開（職権）" />
        <item code="A1IB3492" value="外国語国際公開図面（職権）" />
        <item code="A1IB3493" value="外国語国際公開配列表（職権）" />
        <item code="A1IB350" value="予備審査請求書の提出又は選択無とみなす通知" />
        <item code="A1IB500" value="ＩＢ回答書" />
        <item code="A1IBC101" value="訂正／国際出願の写し" />
        <item code="A1IBC210" value="訂正／国際調査報告" />
        <item code="A1IBC21J" value="訂正／国際調査報告（日本語）" />
        <item code="A1IBC304" value="訂正／優先権主張の書類提出に関する通知" />
        <item code="A1IBC305" value="訂正／先の出願番号の遅れた提出の通知" />
        <item code="A1IBC306" value="訂正／記録の変更通知" />
        <item code="A1IBC307" value="訂正／国際出願又は指定の取り下げの通知" />
        <item code="A1IBC310" value="訂正／送達書類に関する通知（その他雑通知等）" />
        <item code="A1IBC317" value="訂正／優先権に関する取下の通知" />
        <item code="A1IBC31A" value="訂正／優先権書類" />
        <item code="A1IBC31B" value="訂正／条約１９条補正" />
        <item code="A1IBC31C" value="訂正／条約３４条補正" />
        <item code="A1IBC31E" value="訂正／国際予備審査報告（日本語／英語以外の言語）" />
        <item code="A1IBC31J" value="訂正／国際予備審査報告（日本語）" />
        <item code="A1IBC324" value="訂正／指定が取り下げられたものとみなす旨の通知" />
        <item code="A1IBC325" value="訂正／国際出願が取り下げられたものとみなす通知" />
        <item code="A1IBC331" value="訂正／選択の通知" />
        <item code="A1IBC334" value="訂正／後にする選択の届出が提出・選択無とみなす通知" />
        <item code="A1IBC338" value="訂正／国際予備審査報告（英語）" />
        <item code="A1IBC339" value="訂正／予備審査請求又は選択の取り下げの通知" />
        <item code="A1IBC345" value="訂正／他に使用すべき様式がない場合の通知" />
        <item code="A1IBC349" value="訂正／国際公開" />
        <item code="A1IBC350" value="訂正／予備審査請求書の提出又は選択無とみなす通知" />
        <item code="A1IB318" value="優先権主張に関する通知" />
        <item code="A1IB335" value="指定または選択の取り消しの通知" />
        <item code="A1IB346" value="請求の範囲の補正書の提出に関する通知" />
        <item code="A1IB369" value="予備審査請求がされなかった旨の通知" />
        <item code="A1IB373" value="特許性に関する国際予備報告（第Ｉ章）" />
        <item code="A1IB374" value="国際調査機関の見解の翻訳の写しの送付通知" />
        <item code="A1IB399" value="国際出願経過情報様式" />
        <item code="A1IB3494" value="日本語国際公開要約図（職権）" />
        <item code="A1IB3495" value="外国語国際公開要約図（職権）" />
        <item code="A1IB3731" value="非公式コメント" />
        <item code="A1IB501" value="補充国際調査報告" />
        <item code="A1IB502" value="補充国際調査報告を作成しない旨の決定" />
        <item code="A16330" value="明細書" />
        <item code="A16331" value="図面" />
        <item code="A16332" value="要約書" />
        <item code="A16333" value="特許請求の範囲" />
        <item code="A1914" value="出願審査請求手数料返還請求書" />
        <item code="A1915" value="既納手数料返還請求書" />
        <item code="A1916" value="世界知的所有権機関へのアクセスコード付与請求書" />
        <item code="A1603" value="期間延長請求書（期間徒過）" />
        <item code="A1917" value="回復理由書" />
        <item code="A1918" value="保全審査に付することを求める申出書" />
        <item code="A1919" value="不送付通知申出書" />

        <!-- 実用新案 出願系 -->
        <item code="A251" value="'手続補正書（方式）'" />
        <item code="A2521" value="'手続補正書'" />
        <item code="A2522" value="'手続補正書'" />
        <item code="A2523" value="'手続補正書'" />
        <item code="A25210" value="'特許協力条約第３４条補正の翻訳文提出書（職権）'" />
        <item code="A25211" value="'特許協力条約第３４条補正の写し提出書'" />
        <item code="A25212" value="'特許協力条約第３４条補正の写し提出書（職権）'" />
        <item code="A2524" value="'誤訳訂正書'" />
        <item code="A2525" value="'特許協力条約第１９条補正の翻訳文提出書'" />
        <item code="A2526" value="'特許協力条約第１９条補正の翻訳文提出書（職権）'" />
        <item code="A2527" value="'特許協力条約第１９条補正の写し提出書'" />
        <item code="A2528" value="'特許協力条約第１９条補正の写し提出書（職権）'" />
        <item code="A2529" value="'特許協力条約第３４条補正の翻訳文提出書'" />
        <item code="A253" value="'意見書'" />
        <item code="A255" value="'受継申立書'" />
        <item code="A259" value="'弁明書'" />
        <item code="A2601" value="'期間延長請求書'" />
        <item code="A2621" value="'出願審査請求書'" />
        <item code="A2623" value="'実用新案技術評価請求書'" />
        <item code="A2625" value="'出願審査請求書（他人）'" />
        <item code="A2626" value="'国内処理請求書'" />
        <item code="A263" value="'実用新案登録願'" />
        <item code="A2632" value="'国内書面'" />
        <item code="A2633" value="'図面の提出書'" />
        <item code="A2634" value="'国際出願翻訳文提出書'" />
        <item code="A2635" value="'国際出願翻訳文提出書（職権）'" />
        <item code="A2681" value="'代表者選定届'" />
        <item code="A2691" value="'雑書類'" />
        <item code="A2711" value="'出願人名義変更届'" />
        <item code="A2712" value="'出願人名義変更届（一般承継）'" />
        <item code="A27421" value="'代理人変更届'" />
        <item code="A27422" value="'代理人受任届'" />
        <item code="A27423" value="'代理人選任届'" />
        <item code="A27424" value="'代理人辞任届'" />
        <item code="A27425" value="'代理人解任届'" />
        <item code="A27426" value="'代理権変更届'" />
        <item code="A27427" value="'代理権消滅届'" />
        <item code="A27428" value="'包括委任状援用制限届'" />
        <item code="A27431" value="'復代理人変更届'" />
        <item code="A27432" value="'復代理人受任届'" />
        <item code="A27433" value="'復代理人選任届'" />
        <item code="A27434" value="'復代理人辞任届'" />
        <item code="A27435" value="'復代理人解任届'" />
        <item code="A27436" value="'復代理権変更届'" />
        <item code="A27437" value="'復代理権消滅届'" />
        <item code="A2761" value="'出願取下書'" />
        <item code="A2762" value="'出願放棄書'" />
        <item code="A2764" value="'先の出願に基づく優先権主張取下書'" />
        <item code="A2765" value="'パリ条約による優先権主張放棄書'" />
        <item code="A2781" value="'上申書'" />
        <item code="A279" value="'優先権証明書提出書'" />
        <item code="A280" value="'新規性の喪失の例外証明書提出書'" />
        <item code="A2801" value="'新規性喪失の例外適用申請書'" />
        <item code="A281" value="'出願日証明書提出書'" />
        <item code="A282" value="'物件提出書'" />
        <item code="A2821" value="'手続補足書'" />
        <item code="A2822" value="'証明書類提出書'" />
        <item code="A2831" value="'刊行物等提出書'" />
        <item code="A287" value="'優先審査に関する事情説明書'" />
        <item code="A2871" value="'早期審査に関する事情説明書'" />
        <item code="A2872" value="'早期審査に関する事情説明補充書'" />
        <item code="A2IB101" value="'国際出願の写し'" />
        <item code="A2IB101J" value="'国際出願の願書の写し'" />
        <item code="A2IB210" value="'国際調査報告'" />
        <item code="A2IB21J" value="'国際調査報告（日本語）'" />
        <item code="A2IB304" value="'優先権主張の書類提出に関する通知'" />
        <item code="A2IB305" value="'先の出願番号の遅れた提出の通知'" />
        <item code="A2IB306" value="'記録の変更通知'" />
        <item code="A2IB307" value="'国際出願又は指定の取り下げの通知'" />
        <item code="A2IB310" value="'送達書類に関する通知（その他雑通知等）'" />
        <item code="A2IB317" value="'優先権に関する取下の通知'" />
        <item code="A2IB31A" value="'優先権書類'" />
        <item code="A2IB31B" value="'条約１９条補正'" />
        <item code="A2IB31B1" value="'条約１９条補正（職権）'" />
        <item code="A2IB31C" value="'条約３４条補正'" />
        <item code="A2IB31C1" value="'条約３４条補正（職権）'" />
        <item code="A2IB31E" value="'国際予備審査報告（日本語／英語以外の言語）'" />
        <item code="A2IB31J" value="'国際予備審査報告（日本語）'" />
        <item code="A2IB324" value="'指定が取り下げられたものとみなす旨の通知'" />
        <item code="A2IB325" value="'国際出願が取り下げられたものとみなす通知'" />
        <item code="A2IB331" value="'選択の通知'" />
        <item code="A2IB334" value="'後にする選択の届出が提出・選択無とみなす通知'" />
        <item code="A2IB338" value="'国際予備審査報告（英語）'" />
        <item code="A2IB339" value="'予備審査請求又は選択の取り下げの通知'" />
        <item code="A2IB345" value="'他に使用すべき様式がない場合の通知'" />
        <item code="A2IB349" value="'国際公開'" />
        <item code="A2IB3491" value="'日本語国際公開（職権）'" />
        <item code="A2IB3492" value="'外国語国際公開図面（職権）'" />
        <item code="A2IB3493" value="'外国語国際公開配列表（職権）'" />
        <item code="A2IB350" value="'予備審査請求書の提出又は選択無とみなす通知'" />
        <item code="A2IB500" value="'ＩＢ回答書'" />
        <item code="A2IBC101" value="'訂正／国際出願の写し'" />
        <item code="A2IBC210" value="'訂正／国際調査報告'" />
        <item code="A2IBC21J" value="'訂正／国際調査報告（日本語）'" />
        <item code="A2IBC304" value="'訂正／優先権主張の書類提出に関する通知'" />
        <item code="A2IBC305" value="'訂正／先の出願番号の遅れた提出の通知'" />
        <item code="A2IBC306" value="'訂正／記録の変更通知'" />
        <item code="A2IBC307" value="'訂正／国際出願又は指定の取り下げの通知'" />
        <item code="A2IBC310" value="'訂正／送達書類に関する通知（その他雑通知等）'" />
        <item code="A2IBC317" value="'訂正／優先権に関する取下の通知'" />
        <item code="A2IBC31A" value="'訂正／優先権書類'" />
        <item code="A2IBC31B" value="'訂正／条約１９条補正'" />
        <item code="A2IBC31C" value="'訂正／条約３４条補正'" />
        <item code="A2IBC31E" value="'訂正／国際予備審査報告（日本語／英語以外の言語）'" />
        <item code="A2IBC31J" value="'訂正／国際予備審査報告（日本語）'" />
        <item code="A2IBC324" value="'訂正／指定が取り下げられたものとみなす旨の通知'" />
        <item code="A2IBC325" value="'訂正／国際出願が取り下げられたものとみなす通知'" />
        <item code="A2IBC331" value="'訂正／選択の通知'" />
        <item code="A2IBC334" value="'訂正／後にする選択の届出が提出・選択無とみなす通知'" />
        <item code="A2IBC338" value="'訂正／国際予備審査報告（英語）'" />
        <item code="A2IBC339" value="'訂正／予備審査請求又は選択の取り下げの通知'" />
        <item code="A2IBC345" value="'訂正／他に使用すべき様式がない場合の通知'" />
        <item code="A2IBC349" value="'訂正／国際公開'" />
        <item code="A2IBC350" value="'訂正／予備審査請求書の提出又は選択無とみなす通知'" />
        <item code="A2IB318" value="'優先権主張に関する通知'" />
        <item code="A2IB335" value="'指定または選択の取り消しの通知'" />
        <item code="A2IB346" value="'請求の範囲の補正書の提出に関する通知'" />
        <item code="A2IB369" value="'予備審査請求がされなかった旨の通知'" />
        <item code="A2IB373" value="'特許性に関する国際予備報告（第Ｉ章）'" />
        <item code="A2IB374" value="'国際調査機関の見解の翻訳の写しの送付通知'" />
        <item code="A2IB399" value="'国際出願経過情報様式'" />
        <item code="A2IB3494" value="'日本語国際公開要約図（職権）'" />
        <item code="A2IB3495" value="'外国語国際公開要約図（職権）'" />
        <item code="A2IB3731" value="'非公式コメント'" />
        <item code="A2IB501" value="'補充国際調査報告'" />
        <item code="A2IB502" value="'補充国際調査報告を作成しない旨の決定'" />
        <item code="A26330" value="'明細書'" />
        <item code="A26331" value="'図面'" />
        <item code="A26332" value="'要約書'" />
        <item code="A26333" value="'実用新案登録請求の範囲'" />
        <item code="A2915" value="'既納手数料（登録料）返還請求書'" />
        <item code="A2624" value="'実用新案技術評価請求書（他人）'" />
        <item code="A2916" value="'世界知的所有権機関へのアクセスコード付与請求書'" />
        <item code="A2603" value="'期間延長請求書（期間徒過）'" />
        <item code="A2917" value="'回復理由書'" />

        <!-- 意匠 出願系 -->
        <item code="A351" value="'手続補正書（方式）'" />
        <item code="A3523" value="'手続補正書'" />
        <item code="A35231" value="'手続補正書（複数）'" />
        <item code="A353" value="'意見書'" />
        <item code="A355" value="'受継申立書'" />
        <item code="A359" value="'弁明書'" />
        <item code="A3601" value="'期間延長請求書'" />
        <item code="A363" value="'意匠登録願'" />
        <item code="A3630" value="'意匠登録願（複数）'" />
        <item code="A3636" value="'類似意匠登録願'" />
        <item code="A3681" value="'代表者選定届'" />
        <item code="A3691" value="'雑書類'" />
        <item code="A3711" value="'出願人名義変更届'" />
        <item code="A3712" value="'出願人名義変更届（一般承継）'" />
        <item code="A37421" value="'代理人変更届'" />
        <item code="A37422" value="'代理人受任届'" />
        <item code="A37423" value="'代理人選任届'" />
        <item code="A37424" value="'代理人辞任届'" />
        <item code="A37425" value="'代理人解任届'" />
        <item code="A37426" value="'代理権変更届'" />
        <item code="A37427" value="'代理権消滅届'" />
        <item code="A37428" value="'包括委任状援用制限届'" />
        <item code="A37431" value="'復代理人変更届'" />
        <item code="A37432" value="'復代理人受任届'" />
        <item code="A37433" value="'復代理人選任届'" />
        <item code="A37434" value="'復代理人辞任届'" />
        <item code="A37435" value="'復代理人解任届'" />
        <item code="A37436" value="'復代理権変更届'" />
        <item code="A37437" value="'復代理権消滅届'" />
        <item code="A3761" value="'出願取下書'" />
        <item code="A3762" value="'出願放棄書'" />
        <item code="A3765" value="'パリ条約による優先権主張放棄書'" />
        <item code="A37731" value="'出願変更届（独立→類似）'" />
        <item code="A37732" value="'出願変更届（類似→独立）'" />
        <item code="A3781" value="'上申書'" />
        <item code="A379" value="'優先権証明書提出書'" />
        <item code="A380" value="'新規性の喪失の例外証明書提出書'" />
        <item code="A381" value="'出願日証明書提出書'" />
        <item code="A382" value="'物件提出書'" />
        <item code="A3821" value="'手続補足書'" />
        <item code="A3822" value="'証明書類提出書'" />
        <item code="A3824" value="'ひな形又は見本補足書'" />
        <item code="A3833" value="'特徴記載書'" />
        <item code="A3826" value="'意匠法第９条第５項に基づく協議の結果届'" />
        <item code="A3871" value="'早期審査に関する事情説明書'" />
        <item code="A3872" value="'早期審査に関する事情説明補充書'" />
        <item code="A3907" value="'秘密意匠期間変更請求書'" />
        <item code="A3915" value="'既納手数料返還請求書'" />
        <item code="A3603" value="'期間延長請求書（期間徒過）'" />
        <item code="A3917" value="'回復理由書'" />

        <!-- 商標 出願系-->
        <item code="A451" value="'手続補正書（方式）'" />
        <item code="A4523" value="'手続補正書'" />
        <item code="A453" value="'意見書'" />
        <item code="A455" value="'受継申立書'" />
        <item code="A459" value="'弁明書'" />
        <item code="A4601" value="'期間延長請求書'" />
        <item code="A463" value="'商標登録願'" />
        <item code="A4639" value="'団体商標登録願'" />
        <item code="A4632" value="'防護標章登録願'" />
        <item code="A4633" value="'防護標章登録に基づく権利存続期間更新登録願'" />
        <item code="A4634" value="'書換登録申請書'" />
        <item code="A46341" value="'外国語図面'" />
        <item code="A46342" value="'外国語要約書'" />
        <item code="A4635" value="'防護標章登録に基づく権利書換登録申請書'" />
        <item code="A4637" value="'重複登録商標に係る商標権存続期間更新登録願'" />
        <item code="A4638" value="'地域団体商標登録願'" />
        <item code="A4681" value="'代表者選定届'" />
        <item code="A4691" value="'雑書類'" />
        <item code="A4711" value="'出願人名義変更届'" />
        <item code="A4712" value="'出願人名義変更届（一般承継）'" />
        <item code="A4713" value="'出願人名義変更届（特例商標登録出願）'" />
        <item code="A4714" value="'出願人名義変更届（特例商標登録出願）（一般承継）'" />
        <item code="A4715" value="'書換登録申請者名義変更届'" />
        <item code="A47421" value="'代理人変更届'" />
        <item code="A47422" value="'代理人受任届'" />
        <item code="A47423" value="'代理人選任届'" />
        <item code="A47424" value="'代理人辞任届'" />
        <item code="A47425" value="'代理人解任届'" />
        <item code="A47426" value="'代理権変更届'" />
        <item code="A47427" value="'代理権消滅届'" />
        <item code="A47428" value="'包括委任状援用制限届'" />
        <item code="A47431" value="'復代理人変更届'" />
        <item code="A47432" value="'復代理人受任届'" />
        <item code="A47433" value="'復代理人選任届'" />
        <item code="A47434" value="'復代理人辞任届'" />
        <item code="A47435" value="'復代理人解任届'" />
        <item code="A47436" value="'復代理権変更届'" />
        <item code="A47437" value="'復代理権消滅届'" />
        <item code="A4761" value="'出願取下書'" />
        <item code="A4762" value="'出願放棄書'" />
        <item code="A4765" value="'パリ条約による優先権主張放棄書'" />
        <item code="A4766" value="'書換登録申請取下書'" />
        <item code="A4768" value="'使用に基づく特例の適用の主張取下書'" />
        <item code="A4781" value="'上申書'" />
        <item code="A479" value="'優先権証明書提出書'" />
        <item code="A480" value="'出願時の特例証明書提出書'" />
        <item code="A481" value="'出願日証明書提出書'" />
        <item code="A482" value="'物件提出書'" />
        <item code="A4821" value="'手続補足書'" />
        <item code="A4822" value="'証明書類提出書'" />
        <item code="A4831" value="'刊行物等提出書'" />
        <item code="A4871" value="'早期審査に関する事情説明書'" />
        <item code="A4872" value="'早期審査に関する事情説明補充書'" />
        <item code="A4908" value="'協議の結果届'" />
        <item code="A4915" value="'既納手数料返還請求書'" />
        <item code="A4603" value="'期間延長請求書（期間徒過）'" />

        <!-- 登録系 -->
        <item code="R1100" value="特許料納付書" />
        <item code="R120" value="特許料納付書" />
        <item code="R2100" value="実用新案登録料納付書" />
        <item code="R220" value="実用新案登録料納付書" />
        <item code="R3100" value="意匠登録料納付書" />
        <item code="R320" value="意匠登録料納付書" />
        <item code="R4100" value="商標登録料納付書" />
        <item code="R4200" value="商標登録料納付書" />
        <item code="R1101" value="追加の特許の特許料納付書" />
        <item code="R3102" value="類似意匠登録料納付書" />
        <item code="R4103" value="防護標章登録料納付書" />
        <item code="R4104" value="商標更新登録料納付書" />
        <item code="R4105" value="防護標章更新登録料納付書" />
        <item code="R1110" value="特許料納付書（設定補充）" />
        <item code="R2110" value="実用新案登録料納付書（設定補充）" />
        <item code="R3110" value="意匠登録料納付書（設定補充）" />
        <item code="R4110" value="商標登録料納付書（設定補充）" />
        <item code="R1111" value="追加の特許の特許料納付書（設定補充）" />
        <item code="R3112" value="類似意匠登録料納付書（設定補充）" />
        <item code="R4113" value="防護標章登録料納付書（設定補充）" />
        <item code="R4114" value="商標更新登録料納付書（設定補充）" />
        <item code="R4115" value="防護標章更新登録料納付書（設定補充）" />
        <item code="R121" value="特許料納付書（補充）" />
        <item code="R221" value="実用新案登録料納付書（補充）" />
        <item code="R321" value="意匠登録料納付書（補充）" />
        <item code="R4210" value="商標登録料納付書（分納補充）" />
        <item code="R4201" value="商標権存続期間更新登録申請書" />
        <item code="R4211" value="商標権存続期間更新登録申請書（補充）" />
        <item code="R4220" value="手続補足書" />

        <!-- 請求系 -->
        <item code="E1841" value="優先権証明請求書" />
        <item code="E2841" value="優先権証明請求書" />
        <item code="E1842" value="証明請求書" />
        <item code="E2842" value="証明請求書" />
        <item code="E1851" value="ファイル記録事項記載書類の交付請求書" />
        <item code="E2851" value="ファイル記録事項記載書類の交付請求書" />
        <item code="E1852" value="認証付ファイル記録事項記載書類の交付請求書" />
        <item code="E2852" value="認証付ファイル記録事項記載書類の交付請求書" />
        <item code="E1853" value="登録事項記載書類の交付請求書" />
        <item code="E2853" value="登録事項記載書類の交付請求書" />
        <item code="E3853" value="登録事項記載書類の交付請求書" />
        <item code="E4853" value="登録事項記載書類の交付請求書" />
        <item code="E1854" value="認証付登録事項記載書類の交付請求書" />
        <item code="E2854" value="認証付登録事項記載書類の交付請求書" />
        <item code="E3854" value="認証付登録事項記載書類の交付請求書" />
        <item code="E4854" value="認証付登録事項記載書類の交付請求書" />
        <item code="E1861" value="ファイル記録事項の閲覧（縦覧）請求書" />
        <item code="E2861" value="ファイル記録事項の閲覧（縦覧）請求書" />
        <item code="E1862" value="登録事項の閲覧請求書" />
        <item code="E2862" value="登録事項の閲覧請求書" />
        <item code="E3862" value="登録事項の閲覧請求書" />
        <item code="E4862" value="登録事項の閲覧請求書" />

        <!-- 審判系 -->
        <item code="C154" value="回答書" />
        <item code="C254" value="回答書" />
        <item code="C354" value="回答書" />
        <item code="C454" value="回答書" />

        <item code="C1561" value="異議申立書" />
        <item code="C2561" value="異議申立書" />
        <item code="C4561" value="異議申立書" />

        <item code="C157" value="答弁書" />
        <item code="C257" value="答弁書" />
        <item code="C357" value="答弁書" />
        <item code="C457" value="答弁書" />

        <item code="C158" value="弁駁書" />
        <item code="C258" value="弁駁書" />
        <item code="C358" value="弁駁書" />
        <item code="C458" value="弁駁書" />

        <item code="C160" value="審判請求書" />
        <item code="C260" value="審判請求書" />
        <item code="C360" value="審判請求書" />
        <item code="C460" value="審判請求書" />

        <item code="C1601" value="判定請求書" />
        <item code="C2601" value="判定請求書" />
        <item code="C3601" value="判定請求書" />
        <item code="C4601" value="判定請求書" />

        <item code="C1609" value="請求取下書" />
        <item code="C2609" value="請求取下書" />
        <item code="C3609" value="請求取下書" />
        <item code="C4609" value="請求取下書" />

        <item code="C16091" value="一部請求取下書" />
        <item code="C26091" value="一部請求取下書" />
        <item code="C36091" value="一部請求取下書" />
        <item code="C46091" value="一部請求取下書" />

        <item code="C1611" value="訂正請求書" />
        <item code="C2611" value="訂正請求書" />

        <item code="C1619" value="訂正請求取下書" />
        <item code="C2619" value="訂正請求取下書" />

        <item code="C164" value="審理再開申立書" />
        <item code="C264" value="審理再開申立書" />
        <item code="C364" value="審理再開申立書" />
        <item code="C464" value="審理再開申立書" />

        <item code="C16511" value="書面審理申立書" />
        <item code="C26511" value="書面審理申立書" />
        <item code="C36511" value="書面審理申立書" />
        <item code="C46511" value="書面審理申立書" />

        <item code="C16512" value="口頭審理申立書" />
        <item code="C26512" value="口頭審理申立書" />
        <item code="C36512" value="口頭審理申立書" />
        <item code="C46512" value="口頭審理申立書" />

        <item code="C16513" value="口頭審理陳述要領書" />
        <item code="C26513" value="口頭審理陳述要領書" />
        <item code="C36513" value="口頭審理陳述要領書" />
        <item code="C46513" value="口頭審理陳述要領書" />

        <item code="C16514" value="証拠申出書" />
        <item code="C26514" value="証拠申出書" />
        <item code="C36514" value="証拠申出書" />
        <item code="C46514" value="証拠申出書" />

        <item code="C16515" value="証拠説明書" />
        <item code="C26515" value="証拠説明書" />
        <item code="C36515" value="証拠説明書" />
        <item code="C46515" value="証拠説明書" />

        <item code="C16517" value="録音テープ等の内容説明書" />
        <item code="C26517" value="録音テープ等の内容説明書" />
        <item code="C36517" value="録音テープ等の内容説明書" />
        <item code="C46517" value="録音テープ等の内容説明書" />

        <item code="C1652" value="証拠調申立書" />
        <item code="C2652" value="証拠調申立書" />
        <item code="C3652" value="証拠調申立書" />
        <item code="C4652" value="証拠調申立書" />

        <item code="C16541" value="尋問事項書" />
        <item code="C26541" value="尋問事項書" />
        <item code="C36541" value="尋問事項書" />
        <item code="C46541" value="尋問事項書" />

        <item code="C1654" value="証人尋問申出書" />
        <item code="C2654" value="証人尋問申出書" />
        <item code="C3654" value="証人尋問申出書" />
        <item code="C4654" value="証人尋問申出書" />

        <item code="C16542" value="回答希望事項記載書面" />
        <item code="C26542" value="回答希望事項記載書面" />
        <item code="C36542" value="回答希望事項記載書面" />
        <item code="C46542" value="回答希望事項記載書面" />

        <item code="C16543" value="尋問に代わる書面の提出書" />
        <item code="C26543" value="尋問に代わる書面の提出書" />
        <item code="C36543" value="尋問に代わる書面の提出書" />
        <item code="C46543" value="尋問に代わる書面の提出書" />

        <item code="C16544" value="書証の申出書" />
        <item code="C26544" value="書証の申出書" />
        <item code="C36544" value="書証の申出書" />
        <item code="C46544" value="書証の申出書" />

        <item code="C16546" value="文書特定の申出書" />
        <item code="C26546" value="文書特定の申出書" />
        <item code="C36546" value="文書特定の申出書" />
        <item code="C46546" value="文書特定の申出書" />

        <item code="C1655" value="検証申出書" />
        <item code="C2655" value="検証申出書" />
        <item code="C3655" value="検証申出書" />
        <item code="C4655" value="検証申出書" />

        <item code="C1657" value="鑑定の申出書" />
        <item code="C2657" value="鑑定の申出書" />
        <item code="C3657" value="鑑定の申出書" />
        <item code="C4657" value="鑑定の申出書" />

        <item code="C16572" value="鑑定事項書" />
        <item code="C26572" value="鑑定事項書" />
        <item code="C36572" value="鑑定事項書" />
        <item code="C46572" value="鑑定事項書" />

        <item code="C16573" value="鑑定書" />
        <item code="C26573" value="鑑定書" />
        <item code="C36573" value="鑑定書" />
        <item code="C46573" value="鑑定書" />

        <item code="C1659" value="期日変更請求書" />
        <item code="C2659" value="期日変更請求書" />
        <item code="C3659" value="期日変更請求書" />
        <item code="C4659" value="期日変更請求書" />

        <item code="C16591" value="証拠調申請取下書" />
        <item code="C26591" value="証拠調申請取下書" />
        <item code="C36591" value="証拠調申請取下書" />
        <item code="C46591" value="証拠調申請取下書" />

        <item code="C16592" value="不出頭の届出書" />
        <item code="C26592" value="不出頭の届出書" />
        <item code="C36592" value="不出頭の届出書" />
        <item code="C46592" value="不出頭の届出書" />

        <item code="C1661" value="異議取下書" />
        <item code="C2661" value="異議取下書" />
        <item code="C4661" value="異議取下書" />

        <item code="C1662" value="一部異議取下書" />
        <item code="C2662" value="一部異議取下書" />
        <item code="C4662" value="一部異議取下書" />

        <item code="C1875" value="優先審理に関する事情説明書" />
        <item code="C2875" value="優先審理に関する事情説明書" />

        <item code="C1876" value="早期審理に関する事情説明書" />
        <item code="C2876" value="早期審理に関する事情説明書" />
        <item code="C3876" value="早期審理に関する事情説明書" />
        <item code="C4876" value="早期審理に関する事情説明書" />

        <item code="C1877" value="早期審理に関する事情説明補充書" />
        <item code="C2877" value="早期審理に関する事情説明補充書" />
        <item code="C3877" value="早期審理に関する事情説明補充書" />
        <item code="C4877" value="早期審理に関する事情説明補充書" />
    </xsl:variable>

</xsl:stylesheet>