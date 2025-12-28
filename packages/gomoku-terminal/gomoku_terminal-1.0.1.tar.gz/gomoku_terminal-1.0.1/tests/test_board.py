"""
测试棋盘类
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gomoku.board import Board


def test_board_initialization():
    """测试棋盘初始化"""
    board = Board()
    assert board.SIZE == 15
    assert board.move_count == 0
    assert board.last_move is None
    print("✓ 棋盘初始化测试通过")


def test_place_stone():
    """测试落子"""
    board = Board()
    
    # 正常落子
    assert board.place_stone(7, 7, Board.BLACK) == True
    assert board.get_stone(7, 7) == Board.BLACK
    assert board.move_count == 1
    
    # 在已有棋子的位置落子
    assert board.place_stone(7, 7, Board.WHITE) == False
    
    # 超出边界
    assert board.place_stone(-1, 0, Board.BLACK) == False
    assert board.place_stone(15, 15, Board.BLACK) == False
    
    print("✓ 落子测试通过")


def test_check_win_horizontal():
    """测试横向获胜"""
    board = Board()
    
    # 横向连五
    for col in range(5):
        board.place_stone(7, col, Board.BLACK)
    
    assert board.check_win(7, 4) == True
    print("✓ 横向获胜测试通过")


def test_check_win_vertical():
    """测试纵向获胜"""
    board = Board()
    
    # 纵向连五
    for row in range(5):
        board.place_stone(row, 7, Board.WHITE)
    
    assert board.check_win(4, 7) == True
    print("✓ 纵向获胜测试通过")


def test_check_win_diagonal():
    """测试斜向获胜"""
    board = Board()
    
    # 左上到右下
    for i in range(5):
        board.place_stone(i, i, Board.BLACK)
    
    assert board.check_win(4, 4) == True
    print("✓ 斜向获胜测试通过")


def test_get_empty_positions():
    """测试获取空位置"""
    board = Board()
    
    empty = board.get_empty_positions()
    assert len(empty) == 15 * 15
    
    board.place_stone(7, 7, Board.BLACK)
    empty = board.get_empty_positions()
    assert len(empty) == 15 * 15 - 1
    
    print("✓ 获取空位置测试通过")


def test_reset():
    """测试重置棋盘"""
    board = Board()
    
    board.place_stone(7, 7, Board.BLACK)
    board.place_stone(7, 8, Board.WHITE)
    
    board.reset()
    
    assert board.move_count == 0
    assert board.last_move is None
    assert board.get_stone(7, 7) == Board.EMPTY
    
    print("✓ 重置测试通过")


if __name__ == '__main__':
    print("开始运行测试...\n")
    
    test_board_initialization()
    test_place_stone()
    test_check_win_horizontal()
    test_check_win_vertical()
    test_check_win_diagonal()
    test_get_empty_positions()
    test_reset()
    
    print("\n✅ 所有测试通过！")
