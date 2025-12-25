"""
KOSPI/KOSDAQ 마스터 파일 파서

KRX에서 제공하는 종목 마스터 파일(.mst)을 파싱합니다.
"""
import os
import pandas as pd


def parse_kospi_master(base_dir: str) -> pd.DataFrame:
    """KOSPI 마스터 파일 파싱

    Args:
        base_dir (str): kospi_code.mst 파일이 있는 디렉토리

    Returns:
        pd.DataFrame: 종목 정보가 담긴 DataFrame
    """
    file_name = base_dir + "/kospi_code.mst"
    tmp_fil1 = base_dir + "/kospi_code_part1.tmp"
    tmp_fil2 = base_dir + "/kospi_code_part2.tmp"

    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w")

    with open(file_name, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0:len(row) - 228]
            rf1_1 = rf1[0:9].rstrip()
            rf1_2 = rf1[9:21].rstrip()
            rf1_3 = rf1[21:].strip()
            wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')
            rf2 = row[-228:]
            wf2.write(rf2)

    wf1.close()
    wf2.close()

    part1_columns = ['단축코드', '표준코드', '한글명']
    df1 = pd.read_csv(tmp_fil1, header=None, encoding='cp949', names=part1_columns)

    field_specs = [
        2, 1, 4, 4, 4,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 1, 1, 1, 1,
        1, 9, 5, 5, 1,
        1, 1, 2, 1, 1,
        1, 2, 2, 2, 3,
        1, 3, 12, 12, 8,
        15, 21, 2, 7, 1,
        1, 1, 1, 1, 9,
        9, 9, 5, 9, 8,
        9, 3, 1, 1, 1
    ]

    part2_columns = [
        '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',
        '제조업', '저유동성', '지배구조지수종목', 'KOSPI200섹터업종', 'KOSPI100',
        'KOSPI50', 'KRX', 'ETP', 'ELW발행', 'KRX100',
        'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',
        'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',
        'Non1', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',
        'SRI', '기준가', '매매수량단위', '시간외수량단위', '거래정지',
        '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',
        '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',
        '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',
        '상장주수', '자본금', '결산월', '공모가', '우선주',
        '공매도과열', '이상급등', 'KRX300', 'KOSPI', '매출액',
        '영업이익', '경상이익', '당기순이익', 'ROE', '기준년월',
        '시가총액', '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
    ]

    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns)
    df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

    # clean temporary file and dataframe
    del (df1)
    del (df2)
    os.remove(tmp_fil1)
    os.remove(tmp_fil2)
    return df


def parse_kosdaq_master(base_dir: str) -> pd.DataFrame:
    """KOSDAQ 마스터 파일 파싱

    Args:
        base_dir (str): kosdaq_code.mst 파일이 있는 디렉토리

    Returns:
        pd.DataFrame: 종목 정보가 담긴 DataFrame
    """
    file_name = base_dir + "/kosdaq_code.mst"
    tmp_fil1 = base_dir + "/kosdaq_code_part1.tmp"
    tmp_fil2 = base_dir + "/kosdaq_code_part2.tmp"

    wf1 = open(tmp_fil1, mode="w", encoding="cp949")
    wf2 = open(tmp_fil2, mode="w")
    with open(file_name, mode="r", encoding="cp949") as f:
        for row in f:
            rf1 = row[0:len(row) - 222]
            rf1_1 = rf1[0:9].rstrip()
            rf1_2 = rf1[9:21].rstrip()
            rf1_3 = rf1[21:].strip()
            wf1.write(rf1_1 + ',' + rf1_2 + ',' + rf1_3 + '\n')

            rf2 = row[-222:]
            wf2.write(rf2)

    wf1.close()
    wf2.close()

    part1_columns = ['단축코드', '표준코드', '한글명']
    df1 = pd.read_csv(tmp_fil1, header=None, encoding="cp949", names=part1_columns)

    field_specs = [
        2, 1, 4, 4, 4,  # line 20
        1, 1, 1, 1, 1,  # line 27
        1, 1, 1, 1, 1,  # line 32
        1, 1, 1, 1, 1,  # line 38
        1, 1, 1, 1, 1,  # line 43
        1, 9, 5, 5, 1,  # line 48
        1, 1, 2, 1, 1,  # line 54
        1, 2, 2, 2, 3,  # line 64
        1, 3, 12, 12, 8,  # line 69
        15, 21, 2, 7, 1,  # line 75
        1, 1, 1, 9, 9,  # line 80
        9, 5, 9, 8, 9,  # line 85
        3, 1, 1, 1
    ]

    part2_columns = [
        '그룹코드', '시가총액규모', '지수업종대분류', '지수업종중분류', '지수업종소분류',  # line 20
        '벤처기업', '저유동성', 'KRX', 'ETP', 'KRX100',  # line 27
        'KRX자동차', 'KRX반도체', 'KRX바이오', 'KRX은행', 'SPAC',  # line 32
        'KRX에너지화학', 'KRX철강', '단기과열', 'KRX미디어통신', 'KRX건설',  # line 38
        '투자주의', 'KRX증권', 'KRX선박', 'KRX섹터_보험', 'KRX섹터_운송',  # line 43
        'KOSDAQ150', '기준가', '매매수량단위', '시간외수량단위', '거래정지',  # line 48
        '정리매매', '관리종목', '시장경고', '경고예고', '불성실공시',  # line 54
        '우회상장', '락구분', '액면변경', '증자구분', '증거금비율',  # line 64
        '신용가능', '신용기간', '전일거래량', '액면가', '상장일자',  # line 69
        '상장주수', '자본금', '결산월', '공모가', '우선주',  # line 75
        '공매도과열', '이상급등', 'KRX300', '매출액', '영업이익',  # line 80
        '경상이익', '당기순이익', 'ROE', '기준년월', '시가총액',  # line 85
        '그룹사코드', '회사신용한도초과', '담보대출가능', '대주가능'
    ]

    df2 = pd.read_fwf(tmp_fil2, widths=field_specs, names=part2_columns)
    df = pd.merge(df1, df2, how='outer', left_index=True, right_index=True)

    # clean temporary file and dataframe
    del (df1)
    del (df2)
    os.remove(tmp_fil1)
    os.remove(tmp_fil2)
    return df
