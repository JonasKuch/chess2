from chess2.game import Game


game = Game(bot_pth="/Users/jonas/coding/python/chess2/src/chess2/bot/saved_models/model_less_data_leela.pth")
# game.play_bot_vs_bot(sf_side="white", timeout=0.5)
game.play()